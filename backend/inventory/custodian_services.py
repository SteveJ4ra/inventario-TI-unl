"""Corrección de perfil sin reescribir snapshots de movimientos ni revisiones de activos."""
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from .acquisition_services import validated
from .errors import Conflict
from .models import Custodian, CustodianChange
from .serializers import CustodianEditInput
from .services import require_manager

PROFILE_FIELDS = ("full_name", "email", "department")


def profile_snapshot(person):
    return {field: getattr(person, field) for field in PROFILE_FIELDS}


def update_custodian(*, actor, custodian_id, data):
    require_manager(actor)
    values = validated(CustodianEditInput, data)
    expected = values.pop("expected_profile")
    reason = values.pop("reason")
    try:
        with transaction.atomic():
            person = get_object_or_404(Custodian.objects.select_for_update(), pk=custodian_id)
            before = profile_snapshot(person)
            if before != expected:
                raise Conflict("El perfil cambió. Consúltalo antes de repetir.", "stale_profile")
            for field, value in values.items():
                setattr(person, field, value)
            if values:
                person.save(update_fields=list(values))
            CustodianChange.objects.create(custodian=person, actor=actor,
                before_json={"profile": before},
                after_json={"profile": profile_snapshot(person), "reason": reason})
            return person
    except IntegrityError as exc:
        if getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None) == "custodian_email_unique":
            raise Conflict("Ya existe un custodio con ese correo.", "duplicate_custodian") from exc
        raise
