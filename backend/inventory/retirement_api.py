"""API 005; registrar tras integrar proveedores y migraciones reales."""
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.apps import apps
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .errors import Conflict
from .retirement_store import DjangoRetirementStore
from .retirement_models import ReviewerProfile, DecommissionRequest, RetirementAudit, ReviewerAccountAudit
from .retirement_workflow import retire_normal, request_retirement, decide_retirement, reassign_retirement
from .retirement_serializers import NormalRetirementInput, RetirementRequestInput, RetirementDecisionInput, RetirementReassignmentInput, ReviewerCreateInput, ReviewerDeactivateInput, ReviewerPasswordChangeInput
from .retirement_permissions import IsAssignedReviewer, reviewer_has_account
from .serializers import StrictSerializer
from rest_framework import serializers


class LoginInput(StrictSerializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


def valid(cls, data):
    value=cls(data=data);value.is_valid(raise_exception=True);return value.validated_data


def role(user, name):
    if not user.is_authenticated or not DjangoRetirementStore().has_role(user.pk, name):
        raise PermissionDenied("No tienes permiso para esta operación.")


def user_data(user):
    profile=ReviewerProfile.objects.filter(user=user).first()
    temporary=bool(profile and profile.must_change_password)
    permissions=[] if temporary else [name for name in ("manager","operator","reviewer") if DjangoRetirementStore().has_role(user.pk,name)]
    return {"id":user.pk,"username":user.username,"permissions":permissions,"must_change_password":temporary}


def workflow(fn, **kwargs):
    try: return fn(DjangoRetirementStore(), **kwargs)
    except PermissionError as exc: raise PermissionDenied("Acceso denegado.") from exc
    except ValueError as exc: raise Conflict(str(exc)) from exc


@method_decorator(csrf_protect, name="dispatch")
class RetirementLoginView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    def post(self, request):
        data=valid(LoginInput,request.data)
        user=authenticate(request,**data)
        if user is None: raise ValidationError("Usuario o contraseña incorrectos.")
        if not (reviewer_has_account(user) or any(DjangoRetirementStore().has_role(user.pk,name) for name in ("manager","operator"))):
            raise PermissionDenied("Usuario sin acceso autorizado.")
        login(request,user)
        return Response(user_data(user))


class RetirementSessionView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        data=user_data(request.user)
        if not data["permissions"] and not reviewer_has_account(request.user): raise PermissionDenied()
        return Response(data)


class RetirementLogoutView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        logout(request);return Response({"detail":"Sesión cerrada."})


class ReviewerPasswordView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        if not reviewer_has_account(request.user): raise PermissionDenied()
        data=valid(ReviewerPasswordChangeInput,request.data)
        with transaction.atomic():
            user=get_user_model().objects.select_for_update().get(pk=request.user.pk)
            profile=ReviewerProfile.objects.select_for_update().get(user=user)
            if not user.is_active or not user.check_password(data["current_password"]): raise ValidationError("Contraseña actual incorrecta.")
            if data["current_password"] == data["new_password"]: raise ValidationError({"new_password":["Elige una contraseña diferente de la temporal."]})
            try: validate_password(data["new_password"], user=user)
            except DjangoValidationError as exc: raise ValidationError({"new_password":exc.messages}) from exc
            user.set_password(data["new_password"]);user.save(update_fields=["password"])
            profile.must_change_password=False;profile.save(update_fields=["must_change_password"])
            ReviewerAccountAudit.objects.create(user=user,actor=user,action="password_changed",details={"must_change_password":False})
            update_session_auth_hash(request,user)
        return Response({"detail":"Contraseña actualizada."})


class RetireView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, asset_id):
        role(request.user,"manager")
        event=workflow(retire_normal,asset_id=asset_id,actor_id=request.user.pk,**valid(NormalRetirementInput,request.data))
        return Response({"id":event.pk,"movement_id":event.movement_id},status=201)


def request_data(record):
    context=record.context_snapshot
    history=[{"event_type":event.event_type,"occurred_at":event.occurred_at,"resulting_revision":event.resulting_revision,"before":event.before,"after":event.after} for event in RetirementAudit.objects.filter(request=record).order_by("resulting_revision")]
    return {"context":context,"history":history} | {"id":record.pk,"asset_id":record.asset_id,"asset_code":record.asset.code,"reason":record.reason,"status":record.status,"reviewer_id":record.assigned_reviewer_id,"expected_revision":record.asset.revision}


class RetirementRequestsView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, asset_id):
        role(request.user,"manager")
        record=workflow(request_retirement,asset_id=asset_id,actor_id=request.user.pk,**valid(RetirementRequestInput,request.data))
        return Response(request_data(record),status=201)
    def get(self, request, asset_id):
        role(request.user,"manager")
        return Response([request_data(item) for item in DecommissionRequest.objects.filter(asset_id=asset_id).select_related("asset")])


class AssignedRequestsView(APIView):
    permission_classes=[IsAssignedReviewer]
    def get(self, request):
        return Response([request_data(item) for item in DecommissionRequest.objects.filter(assigned_reviewer=request.user).select_related("asset")])


class DecisionView(APIView):
    permission_classes=[IsAssignedReviewer]
    def post(self, request, request_id):
        record=get_object_or_404(DecommissionRequest,pk=request_id,assigned_reviewer=request.user)
        self.check_object_permissions(request,record)
        decision=workflow(decide_retirement,asset_id=record.asset_id,request_id=request_id,actor_id=request.user.pk,**valid(RetirementDecisionInput,request.data))
        return Response({"id":decision.pk,"outcome":decision.outcome},status=201)


class ReassignView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, request_id):
        role(request.user,"operator")
        record=get_object_or_404(DecommissionRequest,pk=request_id)
        result=workflow(reassign_retirement,asset_id=record.asset_id,request_id=request_id,actor_id=request.user.pk,**valid(RetirementReassignmentInput,request.data))
        return Response(request_data(result))


class ReviewersView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        role(request.user,"operator")
        return Response([{"id":p.user_id,"username":p.user.username,"faculty_id":p.faculty_id,"active":p.user.is_active} for p in ReviewerProfile.objects.select_related("user")])
    def post(self, request):
        role(request.user,"operator")
        data=valid(ReviewerCreateInput,request.data)
        faculty=get_object_or_404(apps.get_model("inventory","Faculty"),pk=data["faculty_id"],active=True)
        user=get_user_model()(username=data["username"])
        try: validate_password(data["password"],user=user)
        except DjangoValidationError as exc: raise ValidationError({"password":exc.messages}) from exc
        try:
            with transaction.atomic():
                user.set_password(data["password"]);user.save()
                user.groups.add(Group.objects.get_or_create(name="Revisores")[0])
                ReviewerProfile.objects.create(user=user,faculty=faculty)
                ReviewerAccountAudit.objects.create(user=user,actor=request.user,action="created",details={"username":user.username,"faculty_id":faculty.pk,"faculty_label":faculty.name,"must_change_password":True})
        except IntegrityError as exc:
            if get_user_model().objects.filter(username=data["username"]).exists():
                raise Conflict("El usuario ya existe.","duplicate_user") from exc
            raise
        return Response({"id":user.pk,"username":user.username,"faculty_id":faculty.pk,"must_change_password":True},status=201)


class ReviewerView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self, request, user_id):
        role(request.user,"operator");valid(ReviewerDeactivateInput,request.data)
        with transaction.atomic():
            user=get_object_or_404(get_user_model().objects.select_for_update(),pk=user_id)
            get_object_or_404(ReviewerProfile.objects.select_for_update(),user=user)
            if DecommissionRequest.objects.filter(assigned_reviewer=user,status="pending").exists(): raise Conflict("Reasigna primero las solicitudes pendientes.")
            user.is_active=False;user.save(update_fields=["is_active"])
            ReviewerAccountAudit.objects.create(user=user,actor=request.user,action="deactivated",details={"active":False})
        return Response({"id":user.pk,"active":False})
