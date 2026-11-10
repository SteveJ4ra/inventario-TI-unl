from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework.exceptions import PermissionDenied, ValidationError

from inventory.errors import Conflict
from inventory.models import ImportBatch
from inventory.permissions import is_manager

from . import storage
from .exceptions import (
    ImportDependencyUnavailable,
    ImportDomainConflict,
    ImportDomainValidation,
    ImportPayloadTooLarge,
)
from .parsing import ImportLimitExceeded, parse_import
from .schemas import KINDS

ACTIVE_STATES = (
    ImportBatch.State.INVALID,
    ImportBatch.State.PREVIEW_READY,
    ImportBatch.State.CONFIRMED_ONCE,
)


def _require_manager(actor):
    if not is_manager(actor):
        raise PermissionDenied("Se requiere acceso de gestor autorizado.")


def _require_owner(batch, actor):
    if batch.actor_id != actor.pk:
        raise PermissionDenied("Solo el Gestor que cargó el lote puede consultarlo.")


def _get_locked(batch_id):
    return get_object_or_404(
        ImportBatch.objects.select_for_update(), pk=batch_id
    )


def _expire_locked(batch):
    if (
        batch.state in ACTIVE_STATES
        and batch.expires_at
        and batch.expires_at <= timezone.now()
    ):
        batch.state = ImportBatch.State.EXPIRED
        batch.preview_errors = []
        batch.rows_count = 0
        batch.save(update_fields=["state", "preview_errors", "rows_count"])
        storage.clear_rows(batch)
    return batch


def _check_hash(batch, content_hash):
    if not isinstance(content_hash, str) or not content_hash:
        raise ValidationError(
            {"content_hash": ["Indica el hash de la vista previa."]}
        )
    if content_hash != batch.content_hash:
        raise Conflict(
            "La vista previa cambió. Vuelve a cargar y revisar el archivo.",
            "preview_changed",
        )


def _adapter(kind):
    try:
        adapter_class = import_string(settings.IMPORT_ADAPTERS[kind])
    except (KeyError, ImportError, AttributeError) as exc:
        raise ImportDependencyUnavailable(
            "El adaptador de importación no está configurado."
        ) from exc
    return adapter_class()


def create_preview(*, actor, kind, schema_version, content):
    _require_manager(actor)
    if kind not in KINDS:
        raise ValidationError({"kind": ["Tipo de importación no válido."]})
    try:
        preview = parse_import(
            kind=kind,
            content=content,
            schema_version=schema_version,
            max_bytes=settings.IMPORT_MAX_BYTES,
            max_rows=settings.IMPORT_MAX_ROWS,
        )
    except ImportLimitExceeded as exc:
        raise ImportPayloadTooLarge(str(exc)) from exc
    expires_at = timezone.now() + timedelta(
        minutes=settings.IMPORT_PREVIEW_TTL_MINUTES
    )
    return storage.create_batch(
        actor=actor,
        preview=preview,
        expires_at=expires_at,
    )


def get_batch(*, actor, batch_id):
    _require_manager(actor)
    with transaction.atomic():
        batch = _get_locked(batch_id)
        _require_owner(batch, actor)
        return _expire_locked(batch)


def confirm(*, actor, batch_id, content_hash):
    _require_manager(actor)
    with transaction.atomic():
        batch = _get_locked(batch_id)
        _require_owner(batch, actor)
        _expire_locked(batch)

        if batch.state == ImportBatch.State.CONFIRMED_ONCE:
            _check_hash(batch, content_hash)
            return batch
        if batch.state != ImportBatch.State.PREVIEW_READY:
            raise Conflict(
                "El lote no está listo para confirmar.",
                "invalid_import_state",
            )
        _check_hash(batch, content_hash)
        batch.state = ImportBatch.State.CONFIRMED_ONCE
        batch.confirmed_at = timezone.now()
        batch.save(update_fields=["state", "confirmed_at"])
        return batch


def apply(*, actor, batch_id, content_hash):
    _require_manager(actor)
    with transaction.atomic():
        batch = _get_locked(batch_id)
        _require_owner(batch, actor)
        _expire_locked(batch)

        if batch.state == ImportBatch.State.APPLIED:
            _check_hash(batch, content_hash)
            return batch, False
        if batch.state != ImportBatch.State.CONFIRMED_ONCE:
            raise Conflict(
                "El lote debe confirmarse antes de aplicar.",
                "invalid_import_state",
            )
        _check_hash(batch, content_hash)

        rows = storage.rows_for(batch)
        if not rows or len(rows) != batch.rows_count:
            raise Conflict(
                "La vista previa no conserva las filas necesarias.",
                "preview_incomplete",
            )

        try:
            result = _adapter(batch.kind).apply(rows, actor=actor)
        except ImportDependencyUnavailable as exc:
            raise Conflict(str(exc), "dependency_not_integrated") from exc
        except ImportDomainValidation as exc:
            raise ValidationError(exc.detail) from exc
        except ImportDomainConflict as exc:
            raise Conflict(str(exc), "import_domain_conflict") from exc

        if not isinstance(result, dict):
            raise Conflict(
                "El adaptador no devolvió un resultado verificable.",
                "invalid_adapter_result",
            )

        batch.state = ImportBatch.State.APPLIED
        batch.applied_at = timezone.now()
        batch.applied_result = result
        batch.preview_errors = []
        batch.rows_count = 0
        batch.save(
            update_fields=[
                "state",
                "applied_at",
                "applied_result",
                "preview_errors",
                "rows_count",
            ]
        )
        storage.clear_rows(batch)
        return batch, True


def cancel(*, actor, batch_id):
    _require_manager(actor)
    with transaction.atomic():
        batch = _get_locked(batch_id)
        _require_owner(batch, actor)
        _expire_locked(batch)
        if batch.state == ImportBatch.State.CANCELLED:
            return batch
        if batch.state in (
            ImportBatch.State.APPLIED,
            ImportBatch.State.EXPIRED,
        ):
            raise Conflict(
                "El lote ya no puede cancelarse.",
                "invalid_import_state",
            )
        batch.state = ImportBatch.State.CANCELLED
        batch.preview_errors = []
        batch.rows_count = 0
        batch.save(update_fields=["state", "preview_errors", "rows_count"])
        storage.clear_rows(batch)
        return batch
