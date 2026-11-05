"""Servicios públicos de 006 consumidos por 008; no procesa ni confirma CSV."""

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .services import create_license_lot, require_manager, validate_license_lot


@transaction.atomic
def import_license_lots(*, actor, rows):
    """Crea filas canónicas en la transacción del consumidor, todo o nada."""
    require_manager(actor)
    if not isinstance(rows, list) or not rows:
        raise ValidationError("Se requiere una lista no vacía de lotes.")
    # Validar todo antes de la primera escritura; cada alta vuelve a validar.
    for row in rows:
        validate_license_lot(row)
    for row in rows:
        create_license_lot(actor=actor, data=row)
    return {"kind": "license_lots", "created": len(rows)}
