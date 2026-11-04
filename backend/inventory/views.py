from django.db.models import BigIntegerField, Case, JSONField, OuterRef, Q, Subquery, When
from django.db.models.functions import JSONObject
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from . import services
from .models import (
    Asset, Assignment, Category, Condition, Custodian, Incident, LifecycleStatus,
    MaintenanceEvent, Movement,
)
from .serializers import (
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
        Movement.objects.filter(asset_id=OuterRef("pk"))
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
            When(lifecycle_status=LifecycleStatus.LOCATED, then=Subquery(latest)),
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
        asset = services.create_asset(
            actor=request.user, data=validated(AssetInput, request.data)
        )
        return Response(AssetOutput(asset).data, status=201)


class AssetView(APIView):
    def get(self, request, asset_id):
        return Response(AssetOutput(get_object_or_404(assets(), pk=asset_id)).data)


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


class HistoryView(APIView):
    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, pk=asset_id)
        events = [
            *asset.movements.select_related("actor", "rectified_by"),
            *asset.transitions.all(),
        ]
        events.sort(
            key=lambda event: (
                event.resulting_revision, event.occurred_at,
                getattr(event, "event_type", "movement"), event.pk,
            ),
            reverse=True,
        )
        return Response(HistoryEntry(events, many=True).data)


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
