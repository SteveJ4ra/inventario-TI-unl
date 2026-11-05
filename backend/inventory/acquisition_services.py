"""Servicios de adquisición T006/T008/T011; edición documental y adaptador CSV pendientes.

Orden de locks: documento -> facultad (alta) -> activo -> línea.
No se reasigna una línea/documento ni se cambia origen en este bloque.
"""
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .errors import Conflict
from .models import Asset, AcquisitionDocument, AcquisitionLine, AssetChange, Faculty
from .serializers import (
    AcquisitionDocumentInput, AcquisitionAssetInput, AcquisitionAssociationInput, AssetEditInput,
)
from .services import require_manager, _create_base_asset

DESCRIPTIVE_FIELDS = ("name", "description", "category", "brand", "model", "serial_number")
LINE_FIELDS = ("item_value", "acquired_on", "date_unknown_reason")


def validated(serializer_class, data):
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def reference(model, pk, field, *, lock=False):
    queryset = model.objects.select_for_update() if lock else model.objects.all()
    try:
        return queryset.get(pk=pk)
    except model.DoesNotExist as exc:
        raise ValidationError({field: ["La referencia indicada no existe."]}) from exc


def require_supported_amount(values, field):
    # Límite de implementación, no política monetaria aprobada ni CHECK nuevo.
    if values.get(field) is not None and values[field] <= 0:
        raise Conflict("La política para importes cero/negativos está pendiente de aprobación.", "pending_decision")


def create_document(*, actor, data):
    """Crea el documento y sus asociaciones iniciales como una única operación."""
    require_manager(actor)
    payload = dict(data) if isinstance(data, dict) else data
    values = validated(AcquisitionDocumentInput, payload)
    require_supported_amount(values, "invoice_total")
    if values["source"] == "DONATION" and "document_date" in payload:
        raise Conflict("La fecha documental de donación está pendiente de aprobación.", "pending_decision")
    items = values.pop("items")
    for item in items:
        require_supported_amount(item, "item_value")
    with transaction.atomic():
        document = AcquisitionDocument.objects.create(created_by=actor, **values)
        # Orden global estable incluso cuando dos solicitudes invierten sus items.
        list(Asset.objects.select_for_update().filter(pk__in=[item["asset_id"] for item in items]).order_by("pk"))
        for item in items:
            item = dict(item)
            asset_id = item.pop("asset_id")
            associate_asset(actor=actor, document_id=document.pk, asset_id=asset_id, data=item)
        return document


def create_asset_with_acquisition(*, actor, data):
    require_manager(actor)
    values = validated(AcquisitionAssetInput, data)
    require_supported_amount(values, "item_value")
    document_id = values.pop("acquisition_document_id")
    faculty_id = values.pop("faculty_id")
    line_values = {field: values.pop(field) for field in LINE_FIELDS}
    with transaction.atomic():
        document = reference(AcquisitionDocument, document_id, "acquisition_document_id", lock=True)
        faculty = reference(Faculty, faculty_id, "faculty_id", lock=True)
        asset = _create_base_asset(actor=actor, data={**values, "faculty_id": faculty.pk})
        AcquisitionLine.objects.create(document=document, asset=asset, **line_values)
        return asset


def acquisition_snapshot(asset):
    line = AcquisitionLine.objects.select_related("document").filter(asset_id=asset.pk).first()
    if line is None:
        return None
    document = line.document
    return {
        "document_id": document.pk, "source": document.source, "reference": document.reference,
        "document_date": document.document_date.isoformat() if document.document_date else None,
        "supplier": document.supplier, "support_type": document.support_type,
        "invoice_total": str(document.invoice_total) if document.invoice_total is not None else None,
        "currency": document.currency, "item_value": str(line.item_value),
        "acquired_on": line.acquired_on.isoformat() if line.acquired_on else None,
        "date_unknown_reason": line.date_unknown_reason,
    }


def metadata_snapshot(asset):
    return {**{field: getattr(asset, field) for field in DESCRIPTIVE_FIELDS},
            "acquisition": acquisition_snapshot(asset)}


def check_revision(asset, expected):
    if asset.revision != expected:
        raise Conflict("La ficha cambió. Recárgala antes de repetir.", "stale_revision")


def record_change(asset, actor, reason, before):
    asset.revision += 1
    asset.save(update_fields=["revision"])
    AssetChange.objects.create(asset=asset, actor=actor, reason=reason,
        before_json=before, after_json=metadata_snapshot(asset), resulting_revision=asset.revision)


def associate_asset(*, actor, document_id, asset_id, data):
    """Documenta un activo existente sin adquisición; no reasigna registros vigentes."""
    require_manager(actor)
    values = validated(AcquisitionAssociationInput, data)
    require_supported_amount(values, "item_value")
    expected = values.pop("expected_revision")
    reason = values.pop("reason")
    with transaction.atomic():
        document = reference(AcquisitionDocument, document_id, "acquisition_document_id", lock=True)
        asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
        check_revision(asset, expected)
        if AcquisitionLine.objects.filter(asset=asset).exists():
            raise Conflict("El activo ya tiene adquisición vigente.", "acquisition_exists")
        before = metadata_snapshot(asset)
        line = AcquisitionLine.objects.create(document=document, asset=asset, **values)
        record_change(asset, actor, reason, before)
        return line


def update_asset(*, actor, asset_id, data):
    """Primitiva auditada T006. No expone PATCH ni implementa el flujo web T014."""
    require_manager(actor)
    values = validated(AssetEditInput, data)
    require_supported_amount(values, "item_value")
    expected = values.pop("expected_revision")
    reason = values.pop("reason")
    try:
        with transaction.atomic():
            document_id = AcquisitionLine.objects.filter(asset_id=asset_id).values_list("document_id", flat=True).first()
            if document_id is not None:
                reference(AcquisitionDocument, document_id, "acquisition_document_id", lock=True)
            asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
            line = AcquisitionLine.objects.select_for_update().filter(asset=asset).first()
            if (line.document_id if line else None) != document_id:
                raise Conflict("La adquisición cambió; consulta nuevamente.", "stale_revision")
            check_revision(asset, expected)
            before = metadata_snapshot(asset)
            line_values = {field: values.pop(field) for field in LINE_FIELDS if field in values}
            if line_values and line is None:
                raise ValidationError({"acquisition": ["El activo no tiene adquisición documentada."]})
            for field, value in values.items():
                setattr(asset, field, value)
            if values:
                asset.save(update_fields=list(values))
            if line_values:
                for field, value in line_values.items():
                    setattr(line, field, value)
                line.save(update_fields=list(line_values))
            record_change(asset, actor, reason, before)
            return asset
    except IntegrityError as exc:
        if getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None) == "asset_identity_unique":
            raise Conflict("Ya existe un activo con esa marca, modelo y serie.", "duplicate_asset") from exc
        raise


def get_document(*, actor, document_id):
    """Lectura compartida sin cambiar revisión, valor ni moneda del documento."""
    require_manager(actor)
    return get_object_or_404(AcquisitionDocument.objects.select_related("created_by")
        .prefetch_related("items__asset"), pk=document_id)


def import_assets(*, actor, rows):
    """Contrato proveedor 003/008; comparte reglas y transacción con altas manuales."""
    from .acquisition_imports import import_assets as apply_rows
    return apply_rows(actor=actor, rows=rows)


DOCUMENT_FIELDS = ("source", "reference", "document_date", "supplier", "invoice_total", "support_type", "currency")


def document_snapshot(document):
    return {
        field: (getattr(document, field).isoformat() if field == "document_date" and getattr(document, field)
                else str(getattr(document, field)) if field == "invoice_total" and getattr(document, field) is not None
                else getattr(document, field))
        for field in DOCUMENT_FIELDS
    }


def update_document(*, actor, document_id, data):
    from .serializers import DocumentEditInput
    from .models import AcquisitionDocumentChange
    require_manager(actor)
    values = validated(DocumentEditInput, data)
    expected = values.pop("expected_document")
    expected["document_date"] = expected["document_date"].isoformat() if expected["document_date"] else None
    expected["invoice_total"] = str(expected["invoice_total"]) if expected["invoice_total"] is not None else None
    revisions = values.pop("expected_revisions")
    reason = values.pop("reason")
    with transaction.atomic():
        document = get_object_or_404(AcquisitionDocument.objects.select_for_update(), pk=document_id)
        before_document = document_snapshot(document)
        if expected != before_document:
            raise Conflict("El documento cambió. Consúltalo antes de repetir.", "stale_document")
        assets = list(Asset.objects.select_for_update().filter(acquisition_line__document=document).order_by("pk"))
        if set(revisions) != {str(asset.pk) for asset in assets}:
            raise Conflict("Cambió el conjunto de activos del documento. Consúltalo nuevamente.", "stale_document")
        for asset in assets:
            check_revision(asset, revisions[str(asset.pk)])
        if document.source == "DONATION" and "document_date" in values:
            raise Conflict("La fecha documental de donación sigue pendiente.", "pending_decision")
        allowed = {"reference", "document_date", "supplier", "invoice_total"} if document.source == "PURCHASE" else {"reference", "support_type"}
        disallowed = set(values) - allowed
        if disallowed:
            raise ValidationError({field: ["No corresponde al tipo de adquisición."] for field in disallowed})
        require_supported_amount(values, "invoice_total")
        candidate = {field: getattr(document, field) for field in allowed}
        candidate.update(values)
        candidate["source"] = document.source
        validated(AcquisitionDocumentInput, candidate)
        before_assets = {asset.pk: metadata_snapshot(asset) for asset in assets}
        for field, value in values.items():
            setattr(document, field, value)
        if values:
            document.save(update_fields=list(values))
        for asset in assets:
            record_change(asset, actor, reason, before_assets[asset.pk])
        AcquisitionDocumentChange.objects.create(document=document, actor=actor, reason=reason,
            before_json=before_document, after_json=document_snapshot(document))
        return document
