"""API de importación CSV: plantillas, preview y doble confirmación."""

import re

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import ImportBatch

from . import domain, schemas, services
from .gateways import ProviderUnavailable

HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PAGE_SIZE = 50


class LimitExceeded(APIException):
    status_code = 413
    error_code = "limit_exceeded"


class ServiceUnavailable(APIException):
    status_code = 503
    error_code = "provider_unavailable"


def _payload(batch, *, rows=None, page=1, request=None):
    all_rows = batch.rows if batch.rows is not None else []
    row_count = len(all_rows)
    if rows is None:
        rows = all_rows
    next_url = previous_url = None
    if request is not None and row_count:
        query = request.query_params.copy()
        query["page"] = str(page + 1)
        next_url = (
            request.build_absolute_uri("?" + query.urlencode())
            if page * PAGE_SIZE < row_count
            else None
        )
        if page > 1:
            query["page"] = str(page - 1)
            previous_url = request.build_absolute_uri("?" + query.urlencode())
    return {
        "batch_id": str(batch.pk),
        "kind": batch.kind,
        "schema_version": batch.schema_version,
        "state": batch.state,
        "content_hash": batch.content_hash,
        "summary": batch.preview_summary,
        "errors": batch.errors or [],
        "rows": rows,
        "row_count": row_count,
        "page": page,
        "next": next_url,
        "previous": previous_url,
        "created_at": batch.created_at,
        "expires_at": batch.expires_at,
        "confirmed_at": batch.confirmed_at,
        "applied_at": batch.applied_at,
        "applied_result": batch.applied_result,
    }


def _content_hash(request):
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError("Se requiere un objeto JSON.")
    extra = set(data) - {"content_hash"}
    if extra:
        raise ValidationError(
            {key: ["Campo no permitido."] for key in sorted(extra)}
        )
    value = data.get("content_hash")
    if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
        raise ValidationError(
            {"content_hash": ["Indica el hash de la vista previa."]}
        )
    return value


def _provider(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except ProviderUnavailable as exc:
        raise ServiceUnavailable(str(exc)) from exc


class TemplatesView(APIView):
    def get(self, request, kind):
        if kind not in schemas.KINDS:
            raise Http404("Tipo de importación no encontrado.")
        version = request.query_params.get("schema_version")
        if version and version != schemas.default_version(kind):
            raise ValidationError(
                {"schema_version": ["Versión de plantilla no soportada."]}
            )
        path = services.template_path(kind)
        content = path.read_bytes()
        if not content.startswith(b"\xef\xbb\xbf"):
            content = b"\xef\xbb\xbf" + content
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{schemas.default_version(kind)}.csv"'
        )
        return response


class PreviewsView(APIView):
    def post(self, request):
        kind = request.data.get("kind")
        version = request.data.get("schema_version")
        if kind not in schemas.KINDS:
            raise ValidationError(
                {"kind": ["Elige assets o license_lots."]}
            )
        if version != schemas.default_version(kind):
            raise ValidationError(
                {"schema_version": ["La versión no corresponde al tipo elegido."]}
            )
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": ["Adjunta un archivo CSV."]})
        maximum = int(getattr(settings, "IMPORT_MAX_BYTES", 2_000_000))
        raw = upload.read(maximum + 1)
        if len(raw) > maximum:
            raise LimitExceeded("El archivo supera el tamaño máximo permitido.")
        try:
            batch = _provider(
                services.preview,
                actor=request.user,
                kind=kind,
                schema_version=version,
                raw=raw,
            )
        except domain.CsvLimitExceeded as exc:
            raise LimitExceeded(str(exc)) from exc
        except domain.UnsupportedSchema as exc:
            raise ValidationError({"schema_version": [str(exc)]}) from exc
        body = _payload(batch)
        if batch.state == ImportBatch.State.PREVIEW_READY:
            return Response(body, status=201)
        body = {
            "code": "invalid_batch",
            "detail": "El archivo tiene errores; corrige las filas y vuelve a cargarlo.",
            **body,
        }
        return Response(body, status=400)


class BatchView(APIView):
    def get(self, request, batch_id):
        batch = services.get_batch(actor=request.user, batch_id=batch_id)
        rows = batch.rows if batch.rows is not None else []
        try:
            page = int(request.query_params.get("page", "1"))
        except ValueError:
            raise ValidationError({"page": ["La página no existe."]}) from None
        if page < 1 or (page > 1 and (page - 1) * PAGE_SIZE >= len(rows)):
            raise ValidationError({"page": ["La página no existe."]})
        start = (page - 1) * PAGE_SIZE
        return Response(
            _payload(
                batch,
                rows=rows[start : start + PAGE_SIZE],
                page=page,
                request=request,
            )
        )


class ConfirmView(APIView):
    def post(self, request, batch_id):
        digest = _content_hash(request)
        batch, _changed = _provider(
            services.confirm,
            actor=request.user,
            batch_id=batch_id,
            content_hash=digest,
        )
        return Response(_payload(batch), status=200)


class ApplyView(APIView):
    def post(self, request, batch_id):
        digest = _content_hash(request)
        try:
            batch, created = _provider(
                services.apply,
                actor=request.user,
                batch_id=batch_id,
                content_hash=digest,
            )
        except services.ImportRevalidationFailed as exc:
            return Response(
                {
                    "code": "import_conflict",
                    "detail": (
                        "La base de datos cambió desde la vista previa; "
                        "no se creó ningún registro."
                    ),
                    "errors": exc.errors,
                },
                status=409,
            )
        return Response(_payload(batch), status=201 if created else 200)


class CancelView(APIView):
    def post(self, request, batch_id):
        batch, _changed = _provider(
            services.cancel, actor=request.user, batch_id=batch_id
        )
        return Response(_payload(batch), status=200)
