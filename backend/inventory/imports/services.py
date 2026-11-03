"""Orquestación transaccional del ciclo de importación CSV (008)."""

from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from inventory.errors import Conflict
from inventory.models import ImportBatch

from . import domain, schemas
from .gateways import get_gateway

CONFIRMABLE = (
    ImportBatch.State.INVALID,
    ImportBatch.State.PREVIEW_READY,
    ImportBatch.State.CONFIRMED_ONCE,
)


class ImportRevalidationFailed(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("La base de datos cambió desde la vista previa.")


def _ttl():
    return int(getattr(settings, "IMPORT_PREVIEW_TTL_SECONDS", 86400))


def _limits():
    return (
        int(getattr(settings, "IMPORT_MAX_BYTES", 2_000_000)),
        int(getattr(settings, "IMPORT_MAX_ROWS", 2000)),
    )


def _require_owner(batch, actor):
    if batch.owner_id != getattr(actor, "pk", None):
        raise PermissionDenied("Solo el gestor que cargó el lote puede consultarlo.")


def _expire(batch, now=None):
    now = now or timezone.now()
    if batch.state in CONFIRMABLE and batch.expires_at <= now:
        batch.state = ImportBatch.State.EXPIRED
        batch.rows = None
        batch.errors = []
        batch.save(update_fields=["state", "rows", "errors", "updated_at"])
    return batch


def _revalidate(batch):
    gateway = get_gateway()
    if batch.kind == ImportBatch.Kind.ASSETS:
        return gateway.validate_assets(batch.rows or [])
    return gateway.validate_license_lots(batch.rows or [])


def preview(*, actor, kind, schema_version, raw):
    max_bytes, max_rows = _limits()
    result = domain.parse_csv(
        kind,
        schema_version,
        raw,
        max_bytes=max_bytes,
        max_rows=max_rows,
    )
    errors = list(result.errors)
    rows = result.rows
    summary = result.summary
    digest = result.content_hash
    if not errors:
        reference_errors = _revalidate(
            ImportBatch(
                kind=kind,
                schema_version=schema_version,
                rows=rows,
                content_hash=digest,
            )
        )
        if reference_errors:
            errors = reference_errors
            bad_rows = {error["row"] for error in reference_errors if error["row"]}
            for row in rows:
                if row["row"] in bad_rows:
                    row["valid"] = False
            summary = domain.summarize(kind, rows)
            digest = domain.content_hash(kind, schema_version, rows, summary)

    now = timezone.now()
    state = (
        ImportBatch.State.PREVIEW_READY if not errors else ImportBatch.State.INVALID
    )
    batch = ImportBatch.objects.create(
        owner=actor,
        kind=kind,
        schema_version=schema_version,
        state=state,
        content_hash=digest,
        preview_summary=summary,
        errors=errors,
        rows=rows,
        expires_at=now + timedelta(seconds=_ttl()),
    )
    return batch


def get_batch(*, actor, batch_id):
    batch = get_object_or_404(ImportBatch, pk=batch_id)
    _require_owner(batch, actor)
    return _expire(batch)


def confirm(*, actor, batch_id, content_hash):
    conflict = None
    changed = False
    with transaction.atomic():
        batch = get_object_or_404(
            ImportBatch.objects.select_for_update(), pk=batch_id
        )
        _require_owner(batch, actor)
        _expire(batch)
        if batch.state == ImportBatch.State.APPLIED:
            conflict = ("El lote ya fue aplicado.", "already_applied")
        elif batch.state == ImportBatch.State.CANCELLED:
            conflict = ("El lote fue cancelado.", "cancelled_batch")
        elif batch.state == ImportBatch.State.EXPIRED:
            conflict = (
                "La vista previa venció; carga el archivo de nuevo.",
                "expired_batch",
            )
        elif batch.state == ImportBatch.State.INVALID:
            conflict = (
                "El lote tiene errores y no puede confirmarse.",
                "invalid_batch",
            )
        elif content_hash != batch.content_hash:
            conflict = (
                "El contenido cambió; vuelve a cargar y revisar el archivo.",
                "stale_preview",
            )
        elif batch.state == ImportBatch.State.CONFIRMED_ONCE:
            if content_hash != batch.confirmed_hash:
                conflict = (
                    "La confirmación no corresponde a este contenido.",
                    "stale_preview",
                )
        else:
            batch.state = ImportBatch.State.CONFIRMED_ONCE
            batch.confirmed_hash = content_hash
            batch.confirmed_at = timezone.now()
            batch.save(
                update_fields=[
                    "state",
                    "confirmed_hash",
                    "confirmed_at",
                    "updated_at",
                ]
            )
            changed = True
    if conflict:
        raise Conflict(*conflict)
    return batch, changed


def apply(*, actor, batch_id, content_hash):
    conflict = None
    revalidation_errors = None
    changed = False
    result = None
    with transaction.atomic():
        batch = get_object_or_404(
            ImportBatch.objects.select_for_update(), pk=batch_id
        )
        _require_owner(batch, actor)
        _expire(batch)
        if batch.state == ImportBatch.State.APPLIED:
            pass
        elif batch.state == ImportBatch.State.CANCELLED:
            conflict = ("El lote fue cancelado.", "cancelled_batch")
        elif batch.state == ImportBatch.State.EXPIRED:
            conflict = (
                "La vista previa venció; carga el archivo de nuevo.",
                "expired_batch",
            )
        elif batch.state == ImportBatch.State.INVALID:
            conflict = (
                "El lote tiene errores y no puede aplicarse.",
                "invalid_batch",
            )
        elif batch.state != ImportBatch.State.CONFIRMED_ONCE:
            conflict = (
                "Falta la primera confirmación explícita.",
                "confirmation_required",
            )
        elif (
            not content_hash
            or content_hash != batch.content_hash
            or content_hash != batch.confirmed_hash
        ):
            conflict = (
                "La confirmación no corresponde a este contenido.",
                "stale_preview",
            )
        elif not batch.rows:
            conflict = (
                "El contenido temporal del lote ya no está disponible.",
                "expired_batch",
            )
        else:
            revalidation_errors = _revalidate(batch)
            if not revalidation_errors:
                gateway = get_gateway()
                try:
                    with transaction.atomic():
                        if batch.kind == ImportBatch.Kind.ASSETS:
                            result = gateway.apply_assets(batch.rows, actor)
                        else:
                            result = gateway.apply_license_lots(batch.rows, actor)
                except IntegrityError:
                    conflict = (
                        "Un registro chocó con la base de datos; no se creó nada.",
                        "import_conflict",
                    )
                    revalidation_errors = None
                else:
                    batch.state = ImportBatch.State.APPLIED
                    batch.applied_at = timezone.now()
                    batch.applied_hash = content_hash
                    batch.applied_result = result
                    batch.rows = None
                    batch.errors = []
                    batch.save(
                        update_fields=[
                            "state",
                            "applied_at",
                            "applied_hash",
                            "applied_result",
                            "rows",
                            "errors",
                            "updated_at",
                        ]
                    )
                    changed = True
    if revalidation_errors:
        raise ImportRevalidationFailed(revalidation_errors)
    if conflict:
        raise Conflict(*conflict)
    return batch, changed


def cancel(*, actor, batch_id):
    conflict = None
    changed = False
    with transaction.atomic():
        batch = get_object_or_404(
            ImportBatch.objects.select_for_update(), pk=batch_id
        )
        _require_owner(batch, actor)
        _expire(batch)
        if batch.state == ImportBatch.State.APPLIED:
            conflict = ("El lote ya fue aplicado.", "already_applied")
        elif batch.state == ImportBatch.State.CANCELLED:
            pass
        else:
            batch.state = ImportBatch.State.CANCELLED
            batch.cancelled_at = timezone.now()
            batch.rows = None
            batch.errors = []
            batch.save(
                update_fields=[
                    "state",
                    "cancelled_at",
                    "rows",
                    "errors",
                    "updated_at",
                ]
            )
            changed = True
    if conflict:
        raise Conflict(*conflict)
    return batch, changed


def template_path(kind):
    if kind not in schemas.KINDS:
        raise ValueError("Tipo de importación no soportado.")
    return schemas.TEMPLATE_FILES[kind]
