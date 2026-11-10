from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import service
from .exceptions import ImportPayloadTooLarge
from .schemas import KINDS, SCHEMA_VERSION, template_bytes
from .serializers import ImportBatchOutput

PAGE_SIZE = 50


def _batch_payload(batch):
    return dict(ImportBatchOutput(batch).data)


def _page_number(request):
    raw = request.query_params.get("page", "1")
    try:
        page = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({"page": ["La página no es válida."]})
    if page < 1:
        raise ValidationError({"page": ["La página no es válida."]})
    return page


def _page_url(request, page):
    query = request.query_params.copy()
    query["page"] = str(page)
    return request.build_absolute_uri("?" + query.urlencode())


def _rows_payload(request, batch):
    page = _page_number(request)
    rows = batch.rows.order_by("row_number")
    count = rows.count()
    if page > 1 and (page - 1) * PAGE_SIZE >= count:
        raise ValidationError({"page": ["La página no existe."]})
    results = [
        {"row_number": row.row_number, "values": row.normalized}
        for row in rows[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
    ]
    return {
        "count": count,
        "next": _page_url(request, page + 1) if page * PAGE_SIZE < count else None,
        "previous": _page_url(request, page - 1) if page > 1 else None,
        "results": results,
    }


class ImportTemplateView(APIView):
    def get(self, request, kind):
        if kind not in KINDS:
            raise Http404
        response = HttpResponse(
            template_bytes(kind), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{kind}-{SCHEMA_VERSION}.csv"'
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ImportPreviewsView(APIView):
    def post(self, request):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            raise ValidationError({"file": ["Adjunta un archivo CSV."]})
        if uploaded.size > settings.IMPORT_MAX_BYTES:
            raise ImportPayloadTooLarge(
                f"El archivo supera el límite de {settings.IMPORT_MAX_BYTES} bytes."
            )
        kind = request.data.get("kind")
        schema_version = request.data.get("schema_version", SCHEMA_VERSION)
        batch = service.create_preview(
            actor=request.user,
            kind=kind,
            schema_version=schema_version,
            content=uploaded.read(),
        )
        payload = _batch_payload(batch)
        status_code = 201 if batch.state == batch.State.PREVIEW_READY else 400
        return Response(payload, status=status_code)


class ImportBatchView(APIView):
    def get(self, request, batch_id):
        batch = service.get_batch(actor=request.user, batch_id=batch_id)
        payload = _batch_payload(batch)
        if batch.state not in (
            batch.State.EXPIRED,
            batch.State.CANCELLED,
        ):
            payload["rows"] = _rows_payload(request, batch)
        else:
            payload["rows"] = {
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }
        return Response(payload)


class ImportConfirmView(APIView):
    def post(self, request, batch_id):
        batch = service.confirm(
            actor=request.user,
            batch_id=batch_id,
            content_hash=request.data.get("content_hash"),
        )
        return Response(_batch_payload(batch))


class ImportApplyView(APIView):
    def post(self, request, batch_id):
        batch, created = service.apply(
            actor=request.user,
            batch_id=batch_id,
            content_hash=request.data.get("content_hash"),
        )
        payload = _batch_payload(batch)
        payload["created"] = created
        return Response(payload, status=201 if created else 200)


class ImportCancelView(APIView):
    def post(self, request, batch_id):
        batch = service.cancel(actor=request.user, batch_id=batch_id)
        return Response(_batch_payload(batch))
