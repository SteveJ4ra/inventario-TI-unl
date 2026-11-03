"""Gateway en memoria para las pruebas de la API de importación.

Solo se usa con override_settings en pruebas. Nunca es el gateway de
producción y no crea activos ni lotes reales.
"""

from django.db import IntegrityError


class FakeGateway:
    faculty_ids = set()
    document_ids = set()
    existing_identities = set()
    fail_integrity = False
    fail_validation = False
    apply_calls = []

    @classmethod
    def reset(cls):
        cls.faculty_ids = set()
        cls.document_ids = set()
        cls.existing_identities = set()
        cls.fail_integrity = False
        cls.fail_validation = False
        cls.apply_calls = []

    def validate_assets(self, rows):
        errors = []
        for row in rows:
            values = row["values"]
            if values["faculty_id"] not in type(self).faculty_ids:
                errors.append(
                    {
                        "row": row["row"],
                        "field": "faculty_id",
                        "message": "La facultad indicada no existe.",
                    }
                )
            document_id = values["acquisition_document_id"]
            if document_id and document_id not in type(self).document_ids:
                errors.append(
                    {
                        "row": row["row"],
                        "field": "acquisition_document_id",
                        "message": "El documento de adquisición indicado no existe.",
                    }
                )
            identity = (
                values["brand"].lower(),
                values["model"].lower(),
                values["serial_number"].lower(),
            )
            if identity in type(self).existing_identities:
                errors.append(
                    {
                        "row": row["row"],
                        "field": "serial_number",
                        "message": "Ya existe un activo con esa identidad.",
                    }
                )
        return errors

    def validate_license_lots(self, rows):
        return []

    def apply_assets(self, rows, actor):
        if type(self).fail_integrity:
            raise IntegrityError("duplicate key")
        type(self).apply_calls.append(("assets", len(rows), actor.pk))
        return {
            "kind": "assets",
            "created": len(rows),
            "asset_ids": list(range(1000, 1000 + len(rows))),
        }

    def apply_license_lots(self, rows, actor):
        if type(self).fail_integrity:
            raise IntegrityError("duplicate key")
        type(self).apply_calls.append(("license_lots", len(rows), actor.pk))
        return {
            "kind": "license_lots",
            "created": len(rows),
            "license_lot_ids": list(range(2000, 2000 + len(rows))),
        }
