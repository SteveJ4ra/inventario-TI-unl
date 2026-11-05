from . import custodian_services
from django.db.models import Case, IntegerField, OuterRef, Q, Subquery, When
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from . import services, acquisition_services, faculty_services
from .errors import Conflict, DependencyUnavailable
from .permissions import IsOperator, IsManagerOrOperator
from .models import (Asset, Assignment, Category, Condition, Custodian, Movement,
                     Faculty, AcquisitionDocument, AssetChange, AssetFacultyChange)
from .serializers import (
    AssetOutput,
    ConditionInput,
    CustodianInput,
    CustodianOutput,
    DeliveryInput,
    MovementOutput,
    QueryInput,
    RectificationInput,
    ReturnInput,
    FacultyOutput,
    AcquisitionDocumentOutput,
)


def assets():
    latest = (
        Movement.objects.filter(asset_id=OuterRef("pk"), resulting_revision=OuterRef("revision"))
        .order_by("-id")
        .annotate(
            eligible=Case(
                When(type=Movement.Type.RECTIFICATION, then=None),
                default="id",
                output_field=IntegerField(),
            )
        )
        .values("eligible")[:1]
    )
    return Asset.objects.select_related("current_custodian", "created_by").annotate(
        latest_rectifiable_id=Subquery(latest)
    )


def validated(serializer_class, data):
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class AssetsView(APIView):
    def get(self, request):
        data = validated(QueryInput, request.query_params.dict())
        result = assets()
        for field in ["category", "condition", "assignment", "location"]:
            if field in data:
                result = result.filter(**{field: data[field]})
        if "custodian" in data:
            result = result.filter(current_custodian_id=data["custodian"])
        if data.get("search"):
            search = Q()
            for field in [
                "code",
                "name",
                "brand",
                "model",
                "serial_number",
                "current_custodian__full_name",
                "current_custodian__email",
            ]:
                search |= Q(**{field + "__icontains": data["search"]})
            result = result.filter(search)
        page = data["page"]
        count = result.count()
        if page > 1 and (page - 1) * 50 >= count:
            raise ValidationError({"page": ["La página no existe."]})

        def page_url(n):
            query = request.query_params.copy()
            query["page"] = str(n)
            return request.build_absolute_uri("?" + query.urlencode())

        return Response(
            {
                "count": count,
                "next": page_url(page + 1) if page * 50 < count else None,
                "previous": page_url(page - 1) if page > 1 else None,
                "results": AssetOutput(
                    result[(page - 1) * 50 : page * 50], many=True
                ).data,
            }
        )

    def post(self, request):
        asset = acquisition_services.create_asset_with_acquisition(actor=request.user, data=request.data)
        return Response(AssetOutput(asset).data, status=201)


class AssetView(APIView):
    def get(self, request, asset_id):
        return Response(AssetOutput(get_object_or_404(assets(), pk=asset_id)).data)

    def patch(self, request, asset_id):
        asset = acquisition_services.update_asset(actor=request.user, asset_id=asset_id, data=request.data)
        return Response(AssetOutput(assets().get(pk=asset.pk)).data)


class CustodiansView(APIView):
    def get(self, request):
        return Response(CustodianOutput(Custodian.objects.all(), many=True).data)

    def post(self, request):
        person = services.create_custodian(
            actor=request.user, data=validated(CustodianInput, request.data)
        )
        return Response(CustodianOutput(person).data, status=201)


class OptionsView(APIView):
    def get(self, request):
        choices = lambda enum: [
            {"value": v, "label": label} for v, label in enum.choices
        ]
        return Response(
            {
                "categories": choices(Category),
                "conditions": choices(Condition),
                "assignments": choices(Assignment),
                "locations": list(
                    Asset.objects.order_by("location")
                    .values_list("location", flat=True)
                    .distinct()
                ),
            }
        )


class MovementsView(APIView):
    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, pk=asset_id)
        return Response(
            MovementOutput(
                asset.movements.select_related("actor", "rectified_by").all(), many=True
            ).data
        )


class OperationView(APIView):
    def post(self, request, asset_id, operation):
        options = {
            "deliver": (DeliveryInput, Movement.Type.DELIVERY),
            "return": (ReturnInput, Movement.Type.RETURN),
            "condition": (ConditionInput, Movement.Type.CONDITION),
            "rectify": (RectificationInput, Movement.Type.RECTIFICATION),
        }
        serializer, kind = options[operation]
        data = validated(serializer, request.data)
        asset, movement = services.record_operation(
            asset_id=asset_id, actor=request.user, operation=kind, data=data
        )
        return Response(
            {
                "asset": AssetOutput(assets().get(pk=asset.pk)).data,
                "movement": MovementOutput(movement).data,
            },
            status=201,
        )


class FacultiesView(APIView):
    permission_classes = [IsManagerOrOperator]

    def get(self, request):
        return Response(FacultyOutput(Faculty.objects.filter(active=True), many=True).data)


class OperatorFacultiesView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(FacultyOutput(Faculty.objects.all(), many=True).data)

    def post(self, request):
        faculty = faculty_services.save_faculty(actor=request.user, data=request.data)
        return Response(FacultyOutput(faculty).data, status=201)


class OperatorFacultyView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, faculty_id):
        faculty = faculty_services.save_faculty(actor=request.user, data=request.data, faculty_id=faculty_id)
        return Response(FacultyOutput(faculty).data)


class OperatorAssetFacultyView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, asset_id):
        asset = faculty_services.change_asset_faculty(actor=request.user, asset_id=asset_id, data=request.data)
        return Response(AssetOutput(assets().get(pk=asset.pk)).data)


class AcquisitionsView(APIView):
    def post(self, request):
        document = acquisition_services.create_document(actor=request.user, data=request.data)
        return Response(AcquisitionDocumentOutput(document).data, status=201)


class AcquisitionView(APIView):
    def get(self, request, document_id):
        document = acquisition_services.get_document(actor=request.user, document_id=document_id)
        return Response(AcquisitionDocumentOutput(document).data)

    def patch(self, request, document_id):
        document = acquisition_services.update_document(actor=request.user, document_id=document_id, data=request.data)
        return Response(AcquisitionDocumentOutput(document).data)


class CustodianView(APIView):
    def patch(self, request, custodian_id):
        person = custodian_services.update_custodian(actor=request.user, custodian_id=custodian_id, data=request.data)
        return Response(CustodianOutput(person).data)


class AssetHistoryView(APIView):
    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, pk=asset_id)
        events = []
        for movement in asset.movements.select_related("actor", "rectified_by"):
            data = MovementOutput(movement).data
            events.append({"event_type": "movement", "event_id": movement.pk,
                "occurred_at": movement.occurred_at, "actor": data["actor"],
                "resulting_revision": movement.resulting_revision, "data": data})
        for model, event_type in [(AssetChange, "asset_change"), (AssetFacultyChange, "faculty_change")]:
            for event in model.objects.filter(asset=asset).select_related("actor"):
                events.append({"event_type": event_type, "event_id": event.pk,
                    "occurred_at": event.created_at,
                    "actor": {"id": event.actor_id, "username": event.actor.username},
                    "resulting_revision": event.resulting_revision,
                    "data": {"before": event.before_json, "after": event.after_json, "reason": event.reason}})
        events.sort(key=lambda event: (event["resulting_revision"], event["occurred_at"], event["event_type"], event["event_id"]), reverse=True)
        return Response(events)
