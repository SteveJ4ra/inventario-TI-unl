"""Diagnóstico de legado 003: solo lectura, sin asignaciones ni saneamiento."""
from .models import Asset, Custodian
TEXT_FIELDS = {Asset: ("code", "name", "description", "brand", "model", "serial_number", "location"),
               Custodian: ("full_name", "email")}


def acquisition_preflight():
    invalid = {}
    for model, fields in TEXT_FIELDS.items():
        for field in fields:
            count = model.objects.exclude(**{field + "__regex": r"\S"}).count()
            if count:
                invalid[model._meta.label + "." + field] = count
    missing = list(Asset.objects.filter(faculty__isnull=True).order_by("pk").values("id", "code"))
    return {
        "asset_count": Asset.objects.count(),
        "unmapped_assets": missing,
        "missing_acquisition_count": Asset.objects.filter(acquisition_line__isnull=True).count(),
        "invalid_required_text": invalid,
        "faculty_data_ready": not missing and not invalid,
        "requires_release_review": True,
        "writes_performed": False,
    }
