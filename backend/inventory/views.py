from io import BytesIO
from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from django.db.models import Case, IntegerField, OuterRef, Q, Subquery, When
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from . import services
from .models import (
    Asset,
    Assignment,
    Category,
    Condition,
    Custodian,
    Movement,
    SoftwareLicenseLot,
)
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
    MovementOutput,
    QueryInput,
    RectificationInput,
    ReturnInput,
)


def assets():
    latest = (
        Movement.objects.filter(asset_id=OuterRef("pk"))
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
