"""Proveedor 003 para values normalizados de 008; sin parser CSV ni reglas duplicadas."""
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .errors import Conflict
from .models import AcquisitionDocument, Faculty
from .serializers import AssetInput, AcquisitionLineInput
from .services import require_manager

BASE_FIELDS = ("name", "description", "category", "brand", "model", "serial_number", "location", "condition")
DOCUMENT_FIELDS = ("document_source", "document_reference", "document_date", "supplier", "invoice_total", "support_description")
ALLOWED = set(BASE_FIELDS) | set(DOCUMENT_FIELDS) | {
    "faculty_id", "acquisition_document_id", "document_key", "item_value", "acquired_on", "date_unknown_reason",
}


class ImportAssetInput(AssetInput, AcquisitionLineInput):
    faculty_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        return AcquisitionLineInput.validate(self, attrs)


def prepare_rows(rows):
    from .acquisition_services import validated, require_supported_amount
    from .serializers import AcquisitionDocumentInput
    if not isinstance(rows, list) or not rows:
        raise ValidationError({"rows": ["Se requiere una lista no vacía de filas normalizadas."]})
    prepared, documents = [], {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) - ALLOWED:
            raise ValidationError({"rows": [f"Fila {index}: campos no permitidos."]})
        doc_id, key = row.get("acquisition_document_id"), row.get("document_key")
        if bool(doc_id) == bool(key):
            raise ValidationError({"rows": [f"Fila {index}: usa documento existente o clave local, exclusivamente."]})
        values = validated(ImportAssetInput, {field: row[field] for field in (*BASE_FIELDS, "faculty_id", "item_value",
            "acquired_on", "date_unknown_reason") if field in row})
        require_supported_amount(values, "item_value")
        if doc_id:
            doc_id = serializers.IntegerField(min_value=1).run_validation(doc_id)
            if any(row.get(field) not in (None, "") for field in DOCUMENT_FIELDS):
                raise ValidationError({"rows": [f"Fila {index}: no se corrigen metadatos de un documento existente por CSV."]})
        else:
            key = serializers.CharField(max_length=80).run_validation(key)
            source = row.get("document_source")
            metadata = {"source": source, "reference": row.get("document_reference")}
            if source == "DONATION":
                # El adaptador de una descripción libre a tipo requiere acuerdo humano.
                raise Conflict("La adaptación support_description/support_type de donación nueva sigue pendiente.", "pending_decision")
            metadata.update(document_date=row.get("document_date"), supplier=row.get("supplier"), invoice_total=row.get("invoice_total"))
            if row.get("support_description"):
                raise ValidationError({"support_description": ["No corresponde a una compra."]})
            document = validated(AcquisitionDocumentInput, metadata)
            document.pop("items")
            document.pop("support_type")
            require_supported_amount(document, "invoice_total")
            if key in documents and documents[key] != document:
                raise ValidationError({"document_key": ["Los metadatos de la clave local no coinciden."]})
            documents[key] = document
        prepared.append((doc_id, key, values))
    return prepared, documents


def import_assets(*, actor, rows):
    from .acquisition_services import create_document, create_asset_with_acquisition, reference
    require_manager(actor)
    prepared, metadata = prepare_rows(rows)
    with transaction.atomic():
        # Todos los documentos existentes antes de todas las facultades, por id.
        for pk in sorted({row[0] for row in prepared if row[0]}):
            reference(AcquisitionDocument, pk, "acquisition_document_id", lock=True)
        for pk in sorted({row[2]["faculty_id"] for row in prepared}):
            reference(Faculty, pk, "faculty_id", lock=True)
        documents = {key: create_document(actor=actor, data={
            **values, "document_date": values["document_date"].isoformat(),
            "invoice_total": str(values["invoice_total"]),
        }) for key, values in metadata.items()}
        created, used = [], set()
        for doc_id, key, values in prepared:
            document_id = doc_id or documents[key].pk
            asset = create_asset_with_acquisition(actor=actor, data={**values,
                "acquired_on": values["acquired_on"].isoformat() if values["acquired_on"] else None,
                "item_value": str(values["item_value"]), "acquisition_document_id": document_id})
            created.append(asset.pk)
            used.add(document_id)
        return {"created": len(created), "asset_ids": created, "document_ids": sorted(used)}
