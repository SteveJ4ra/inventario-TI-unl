"""Datos de prueba de recuperación sobre los modelos reales."""
from inventory.models import RecoveryEvent


def create_recovery(*, asset, incident):
    return RecoveryEvent.objects.create(
        asset=asset, incident=incident, found_by=incident.reported_by,
        inspected_condition=asset.condition, recovered_location=asset.location,
    )
