from django.db.models import BigIntegerField, Case, JSONField, OuterRef, Q, Subquery, When
from django.db.models.functions import JSONObject
from io import BytesIO
from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError

import segno
from django.http import HttpResponse

from .permissions import IsManager
from .qr_urls import build_asset_qr_url
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from . import services
from .models import (
    Asset, Assignment, Category, Condition, Custodian, Incident, LifecycleStatus,
    MaintenanceEvent, Movement, SoftwareLicenseLot,
)
from . import acquisition_services, faculty_services, custodian_services
from .errors import DependencyUnavailable
from .permissions import IsOperator, IsManagerOrOperator
from .models import AcquisitionDocument, AssetChange, AssetFacultyChange, Faculty
from .serializers import (
    LicenseLotOutput,
    LicenseLotQuery,
    LicenseHistoryQuery,
    LicenseLotAuditOutput,
    AssetInput,
    AssetOutput,
    ConditionInput,
    CustodianInput,
    CustodianOutput,
    DeliveryInput,
    HistoryEntry,
    IncidentInput,
    IncidentOutput,
    IncidentResolutionInput,
    MaintenanceDetail,
    MaintenanceStartInput,
    MaintenanceCloseInput,
    MovementOutput,
    QueryInput,
    RectificationInput,
    RecoveryInput,
    RecoveryOutput,
    ReturnInput,
    FacultyOutput,
    AcquisitionDocumentOutput,
)


def assets():
    last_known = (
        Incident.objects.filter(
            asset_id=OuterRef("pk"), type__in=Incident.LOSS_TYPES, status=Incident.Status.OPEN
        )
        .order_by("-reported_at", "-pk")
        .annotate(
            snapshot=JSONObject(
                lifecycle_status="last_lifecycle_status",
                assignment="last_assignment",
                condition="last_condition",
                location="last_location",
                custodian="last_custodian_snapshot",
            )
        )
        .values("snapshot")[:1]
    )
    active = MaintenanceEvent.objects.filter(
        asset_id=OuterRef("pk"), status=MaintenanceEvent.Status.IN_PROGRESS
    ).values("pk")[:1]
    latest = (
        Movement.objects.filter(asset_id=OuterRef("pk"), resulting_revision=OuterRef("revision"))
        .order_by("-id")
        .annotate(
            eligible=Case(
                When(
                    ~Q(type=Movement.Type.RECTIFICATION),
                    resulting_revision=OuterRef("revision"),
                    rectified_by__isnull=True,
                    then="id",
                ),
                output_field=BigIntegerField(),
            )
        )
        .values("eligible")[:1]
    )
    return Asset.objects.select_related("current_custodian", "created_by").annotate(
        active_maintenance_id=Subquery(active),
        last_known=Case(
            When(lifecycle_status=LifecycleStatus.UNLOCATED, then=Subquery(last_known)),
            output_field=JSONField(),
        ),
        latest_rectifiable_id=Case(
            When(lifecycle_status__in=[LifecycleStatus.LOCATED, LifecycleStatus.RETIRED], then=Subquery(latest)),
            output_field=BigIntegerField(),
        )
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
        if data.get("assignment") == Assignment.AVAILABLE:
            result = result.filter(active_maintenance_id__isnull=True)
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


class IncidentsView(APIView):
    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, pk=asset_id)
        incidents = (
            asset.incidents.select_related("reported_by", "resolved_by")
            .order_by("-reported_at", "-id")
        )
        return Response(IncidentOutput(incidents, many=True).data)

    def post(self, request, asset_id):
        incident = services.report_incident(
            asset_id=asset_id,
            actor=request.user,
            data=validated(IncidentInput, request.data),
        )
        return Response(IncidentOutput(incident).data, status=201)


class IncidentResolutionView(APIView):
    def post(self, request, incident_id):
        incident = services.resolve_incident(
            incident_id=incident_id,
            actor=request.user,
            data=validated(IncidentResolutionInput, request.data),
        )
        return Response(IncidentOutput(incident).data)


class AssetRecoveryView(APIView):
    def post(self, request, asset_id):
        _, recovery = services.recover_asset(
            asset_id=asset_id, actor=request.user,
            data=validated(RecoveryInput, request.data),
        )
        return Response(RecoveryOutput(recovery).data, status=201)


class MaintenanceStartView(APIView):
    def post(self, request, asset_id):
        asset, event = services.start_maintenance(
            asset_id=asset_id, actor=request.user,
            data=validated(MaintenanceStartInput, request.data),
        )
        event.asset = asset
        return Response(MaintenanceDetail(event).data, status=201)


class MaintenanceDetailView(APIView):
    def get(self, request, maintenance_id):
        maintenance = get_object_or_404(
            MaintenanceEvent.objects.select_related("asset"), pk=maintenance_id
        )
        return Response(MaintenanceDetail(maintenance).data)


class MaintenanceCloseView(APIView):
    def post(self, request, maintenance_id):
        asset, event = services.close_maintenance(
            maintenance_id=maintenance_id, actor=request.user,
            data=validated(MaintenanceCloseInput, request.data),
        )
        event.asset = asset
        return Response(MaintenanceDetail(event).data)


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
        events = list(HistoryEntry([
            *asset.movements.select_related("actor", "rectified_by"),
            *asset.transitions.all(),
        ], many=True).data)
        for model, event_type in [(AssetChange, "asset_change"), (AssetFacultyChange, "faculty_change")]:
            for event in model.objects.filter(asset=asset).select_related("actor"):
                events.append({"event_type": event_type, "event_id": event.pk,
                    "occurred_at": event.created_at,
                    "actor": {"id": event.actor_id, "username": event.actor.username},
                    "resulting_revision": event.resulting_revision,
                    "data": {"before": event.before_json, "after": event.after_json, "reason": event.reason}})
        events.sort(key=lambda event: (event["resulting_revision"], event["occurred_at"], event["event_type"], event["event_id"]), reverse=True)
        return Response(events)
def license_page(request, queryset, page, output, *, context=None):
    """Paginación acotada, con el mismo tamaño y envoltura que 002."""
    count = queryset.count()
    if page > 1 and (page - 1) * 50 >= count:
        raise ValidationError({"page": ["La página no existe."]})

    def url(number):
        query = request.query_params.copy()
        query["page"] = str(number)
        return request.build_absolute_uri("?" + query.urlencode())

    return Response(
        {
            "count": count,
            "next": url(page + 1) if page * 50 < count else None,
            "previous": url(page - 1) if page > 1 else None,
            "results": output(
                queryset[(page - 1) * 50 : page * 50], many=True, context=context or {}
            ).data,
        }
    )


class LicenseLotJSONParser(JSONParser):
    # Los siete campos de un lote caben holgadamente en 16 KiB.
    # Se limita la lectura real, incluso sin Content-Length fiable.
    def parse(self, stream, media_type=None, parser_context=None):
        encoding = (parser_context or {}).get("encoding", "utf-8")
        if encoding.lower().replace("_", "-") not in {"utf-8", "utf8"}:
            raise ParseError("La API de licencias requiere JSON UTF-8.")
        raw = stream.read(16385)
        if len(raw) > 16384:
            raise ParseError("El cuerpo JSON del lote supera el límite de 16 KiB.")
        try:
            return super().parse(
                BytesIO(raw), media_type=media_type, parser_context=parser_context
            )
        except RecursionError as exc:
            raise ParseError("El JSON contiene demasiados niveles de anidación.") from exc


class LicenseBaseView(APIView):
    parser_classes = [LicenseLotJSONParser]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class LicenseLotsView(LicenseBaseView):
    def get(self, request):

        data = validated(LicenseLotQuery, request.query_params.dict())
        today = timezone.localdate()
        result = SoftwareLicenseLot.objects.select_related("created_by")
        if data.get("search"):
            result = result.filter(
                Q(product_name__icontains=data["search"])
                | Q(vendor__icontains=data["search"])
            )
        if "license_model" in data:
            result = result.filter(license_model=data["license_model"])
        if data.get("temporal_status") == "NOT_STARTED":
            result = result.filter(starts_on__gt=today)
        elif data.get("temporal_status") == "EXPIRED":
            result = result.filter(ends_on__lt=today)
        elif data.get("temporal_status") == "CURRENT":
            result = result.filter(starts_on__lte=today).filter(
                Q(ends_on__isnull=True) | Q(ends_on__gte=today)
            )
        return license_page(
            request, result, data["page"], LicenseLotOutput, context={"today": today}
        )

    def post(self, request):

        lot = services.create_license_lot(actor=request.user, data=request.data)
        return Response(LicenseLotOutput(lot).data, status=201)


class LicenseLotView(LicenseBaseView):
    def get(self, request, lot_id):

        lot = get_object_or_404(
            SoftwareLicenseLot.objects.select_related("created_by"), pk=lot_id
        )
        return Response(LicenseLotOutput(lot).data)

    def patch(self, request, lot_id):

        lot = services.update_license_lot(
            lot_id=lot_id, actor=request.user, data=request.data
        )
        return Response(LicenseLotOutput(lot).data)


class LicenseLotHistoryView(LicenseBaseView):
    def get(self, request, lot_id):

        data = validated(LicenseHistoryQuery, request.query_params.dict())
        lot = get_object_or_404(SoftwareLicenseLot, pk=lot_id)
        return license_page(
            request,
            lot.audits.select_related("actor"),
            data["page"],
            LicenseLotAuditOutput,
        )
class AssetQrView(APIView):
    """Genera y descarga el QR SVG de un activo."""

    permission_classes = [IsManager]

    def get(self, request, asset_id):
        asset = get_object_or_404(assets(), pk=asset_id)

        # Construir enlace a partir del código TI.
        url = build_asset_qr_url(asset.code)

        # Generar QR bajo demanda.
        qr = segno.make_qr(url, error="M")

        buffer = BytesIO()
        qr.save(buffer, kind="svg", scale=5)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="image/svg+xml",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="activo-{asset.pk}.svg"'
        )
        response["Cache-Control"] = "no-store"
        response["X-Content-Type-Options"] = "nosniff"

        return response


class AssetByCodeView(APIView):
    """Busca un activo mediante su código TI exacto."""

    permission_classes = [IsManager]

    def get(self, request, code):
        asset = get_object_or_404(assets(), code=code)

        return Response(AssetOutput(asset).data)
