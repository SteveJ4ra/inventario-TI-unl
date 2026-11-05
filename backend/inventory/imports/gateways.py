"""Frontera con los paquetes proveedores 003 y 006.

La importación no duplica reglas de adquisición ni de licencias. En producción
este módulo busca los modelos y los servicios de importación de esos paquetes.
Mientras no estén integrados, se informa una indisponibilidad explícita: nunca
se simula una creación exitosa.
"""

from importlib import import_module

from django.conf import settings
from django.utils.module_loading import import_string


class ProviderUnavailable(Exception):
    """Las dependencias 003/006 todavía no exponen el contrato de importación."""


def get_gateway():
    return import_string(settings.IMPORT_GATEWAY)()


class DjangoProviderGateway:
    """Adaptador de producción sobre los contratos publicados por 003/006."""

    ASSET_MODELS = ("Faculty", "AcquisitionDocument", "AcquisitionLine", "Asset")
    LICENSE_MODELS = ("SoftwareLicenseLot",)

    def _model(self, name):
        from django.apps import apps

        try:
            return apps.get_model("inventory", name)
        except LookupError as exc:
            raise ProviderUnavailable(
                f"El paquete proveedor no está integrado: falta el modelo {name}."
            ) from exc

    def _require_models(self, names):
        models = [self._model(name) for name in names]
        # 003 puede preparar modelos antes de revisar/aplicar su migración.
        # Conservar la indisponibilidad explícita también durante esa etapa.
        from django.db import connection

        tables = set(connection.introspection.table_names())
        missing = [model._meta.db_table for model in models if model._meta.db_table not in tables]
        if missing:
            raise ProviderUnavailable(
                "El esquema proveedor no está integrado: faltan tablas " + ", ".join(missing) + "."
            )
        return models

    def _service(self, module_name, function_name):
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as exc:
            # Un import interno roto es un error del proveedor, no su ausencia.
            if not exc.name or not (
                exc.name == module_name or module_name.startswith(exc.name + ".")
            ):
                raise
            raise ProviderUnavailable(
                "El paquete proveedor no está integrado: falta "
                f"{module_name}.{function_name}."
            ) from exc
        function = getattr(module, function_name, None)
        if function is None:
            raise ProviderUnavailable(
                "El paquete proveedor no publica "
                f"{module_name}.{function_name}."
            )
        if not callable(function):
            raise TypeError(f"{module_name}.{function_name} debe ser invocable.")
        return function

    def validate_assets(self, rows):
        Faculty, AcquisitionDocument, _line, Asset = self._require_models(
            self.ASSET_MODELS
        )
        errors = []
        faculty_ids = {
            row["values"]["faculty_id"]
            for row in rows
            if row["values"]["faculty_id"]
        }
        documents = {
            row["values"]["acquisition_document_id"]
            for row in rows
            if row["values"]["acquisition_document_id"]
        }
        existing_faculties = set(
            Faculty.objects.filter(pk__in=faculty_ids).values_list("pk", flat=True)
        )
        existing_documents = set(
            AcquisitionDocument.objects.filter(pk__in=documents).values_list(
                "pk", flat=True
            )
        )
        for row in rows:
            values = row["values"]
            number = row["row"]
            if values["faculty_id"] and values["faculty_id"] not in existing_faculties:
                errors.append(
                    {
                        "row": number,
                        "field": "faculty_id",
                        "message": "La facultad indicada no existe.",
                    }
                )
            document_id = values["acquisition_document_id"]
            if document_id and document_id not in existing_documents:
                errors.append(
                    {
                        "row": number,
                        "field": "acquisition_document_id",
                        "message": "El documento de adquisición indicado no existe.",
                    }
                )
            identity = (
                values["brand"],
                values["model"],
                values["serial_number"],
            )
            if all(identity) and Asset.objects.filter(
                brand__iexact=identity[0],
                model__iexact=identity[1],
                serial_number__iexact=identity[2],
            ).exists():
                errors.append(
                    {
                        "row": number,
                        "field": "serial_number",
                        "message": (
                            "Ya existe un activo con esa marca, modelo y "
                            "número de serie."
                        ),
                    }
                )
        return errors

    def validate_license_lots(self, rows):
        self._require_models(self.LICENSE_MODELS)
        return []

    def apply_assets(self, rows, actor):
        function = self._service(
            "inventory.acquisition_services", "import_assets"
        )
        return function(
            actor=actor, rows=[row["values"] for row in rows]
        )

    def apply_license_lots(self, rows, actor):
        function = self._service(
            "inventory.license_services", "import_license_lots"
        )
        return function(
            actor=actor, rows=[row["values"] for row in rows]
        )
