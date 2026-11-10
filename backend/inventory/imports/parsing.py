import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from .schemas import (
    ACQUISITION_SOURCES,
    ASSET_DOCUMENT_METADATA,
    CATEGORY_VALUES,
    CONDITION_VALUES,
    KIND_ASSETS,
    KIND_LICENSE_LOTS,
    LICENSE_MODEL_VALUES,
    SCHEMA_VERSION,
    fields_for_kind,
)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECIMAL_PATTERN = re.compile(r"^\d{1,12}(?:\.\d{1,2})?$")
MAX_MONEY = Decimal("999999999999.99")


class ImportLimitExceeded(Exception):
    pass


@dataclass(frozen=True)
class RowError:
    row: int
    field: str
    message: str

    def as_dict(self):
        return {"row": self.row, "field": self.field, "message": self.message}


@dataclass(frozen=True)
class Preview:
    kind: str
    schema_version: str
    rows: tuple
    errors: tuple
    summary: dict
    content_hash: str


def canonical_hash(kind, schema_version, rows):
    payload = json.dumps(
        {
            "kind": kind,
            "schema_version": schema_version,
            "rows": list(rows),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _preview(kind, schema_version, rows, errors):
    rows = tuple(rows)
    errors = tuple(errors)
    error_rows = {error.row for error in errors}
    valid = [row for row in rows if row["row_number"] not in error_rows]
    summary = {
        "row_count": len(rows),
        "valid_rows": len(valid),
        "invalid_rows": len(rows) - len(valid),
        "error_count": len(errors),
    }
    if kind == KIND_ASSETS:
        summary["document_count"] = len(
            {row["document_key"] for row in valid if row.get("document_key")}
        )
    if kind == KIND_LICENSE_LOTS:
        summary["purchased_quantity"] = sum(
            row.get("purchased_quantity") or 0 for row in valid
        )
        summary["in_use_quantity"] = sum(
            row.get("in_use_quantity") or 0 for row in valid
        )
    return Preview(
        kind=kind,
        schema_version=schema_version,
        rows=rows,
        errors=errors,
        summary=summary,
        content_hash=canonical_hash(kind, schema_version, rows),
    )


def _text(values, field, errors, row, *, maximum, required=True):
    value = (values.get(field) or "").strip()
    if not value:
        if required:
            errors.append(RowError(row, field, "Este campo es obligatorio."))
        return ""
    if len(value) > maximum:
        errors.append(
            RowError(row, field, f"No puede superar {maximum} caracteres.")
        )
    return value


def _choice(values, field, errors, row, allowed, *, required=True):
    value = _text(values, field, errors, row, maximum=64, required=required)
    if value and value not in allowed:
        errors.append(RowError(row, field, "El valor no está permitido."))
    return value


def _integer(values, field, errors, row, *, minimum=0, required=True):
    value = _text(values, field, errors, row, maximum=20, required=required)
    if not value:
        return None
    if not value.isdigit():
        errors.append(RowError(row, field, "Debe ser un entero válido."))
        return None
    number = int(value)
    if number < minimum:
        errors.append(RowError(row, field, f"Debe ser mayor o igual a {minimum}."))
    return number


def _decimal(values, field, errors, row, *, required=True):
    value = _text(values, field, errors, row, maximum=20, required=required)
    if not value:
        return ""
    if not DECIMAL_PATTERN.fullmatch(value):
        errors.append(
            RowError(row, field, "Usa un monto positivo con hasta dos decimales.")
        )
        return ""
    try:
        number = Decimal(value)
    except InvalidOperation:
        errors.append(RowError(row, field, "El monto no es válido."))
        return ""
    if number > MAX_MONEY:
        errors.append(RowError(row, field, "El monto excede el máximo admitido."))
        return ""
    return f"{number:.2f}"


def _date(values, field, errors, row, *, required=True):
    value = _text(values, field, errors, row, maximum=10, required=required)
    if not value:
        return ""
    if not DATE_PATTERN.fullmatch(value):
        errors.append(RowError(row, field, "Usa una fecha AAAA-MM-DD."))
        return ""
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(RowError(row, field, "La fecha no existe en el calendario."))
        return ""
    return value


def _validate_asset(values, row):
    errors = []
    normalized = {
        "row_number": row,
        "name": _text(values, "name", errors, row, maximum=160),
        "description": _text(values, "description", errors, row, maximum=2000),
        "category": _choice(values, "category", errors, row, CATEGORY_VALUES),
        "brand": _text(values, "brand", errors, row, maximum=120),
        "model": _text(values, "model", errors, row, maximum=120),
        "serial_number": _text(
            values, "serial_number", errors, row, maximum=160
        ),
        "location": _text(values, "location", errors, row, maximum=240),
        "condition": _choice(values, "condition", errors, row, CONDITION_VALUES),
        "faculty_id": _integer(values, "faculty_id", errors, row, minimum=1),
        "acquisition_document_id": _integer(
            values, "acquisition_document_id", errors, row, minimum=1, required=False
        ),
        "document_key": _text(
            values, "document_key", errors, row, maximum=64, required=False
        ),
        "acquisition_source": _choice(
            values,
            "acquisition_source",
            errors,
            row,
            ACQUISITION_SOURCES,
            required=False,
        ),
        "document_reference": _text(
            values, "document_reference", errors, row, maximum=200, required=False
        ),
        "document_date": _date(
            values, "document_date", errors, row, required=False
        ),
        "supplier": _text(
            values, "supplier", errors, row, maximum=160, required=False
        ),
        "invoice_total": _decimal(
            values, "invoice_total", errors, row, required=False
        ),
        "donation_support_type": _text(
            values,
            "donation_support_type",
            errors,
            row,
            maximum=120,
            required=False,
        ),
        "acquired_on": _date(values, "acquired_on", errors, row, required=False),
        "date_unknown_reason": _text(
            values,
            "date_unknown_reason",
            errors,
            row,
            maximum=2000,
            required=False,
        ),
        "item_value": _decimal(values, "item_value", errors, row),
    }

    has_existing_document = bool(normalized["acquisition_document_id"])
    has_document_key = bool(normalized["document_key"])
    if has_existing_document == has_document_key:
        errors.append(
            RowError(
                row,
                "acquisition_document_id",
                "Indica un documento existente o una document_key nueva, no ambos.",
            )
        )

    if has_existing_document:
        if any(normalized[field] for field in ASSET_DOCUMENT_METADATA):
            errors.append(
                RowError(
                    row,
                    "acquisition_document_id",
                    "Los metadatos del documento solo se permiten para una document_key nueva.",
                )
            )
    elif has_document_key:
        source = normalized["acquisition_source"]
        if not source:
            errors.append(
                RowError(
                    row,
                    "acquisition_source",
                    "Indica purchase o donation para la document_key.",
                )
            )
        if not normalized["document_reference"]:
            errors.append(
                RowError(
                    row,
                    "document_reference",
                    "La referencia del documento es obligatoria.",
                )
            )
        if source == "purchase":
            for field in ("document_date", "supplier", "invoice_total"):
                if not normalized[field]:
                    errors.append(
                        RowError(
                            row,
                            field,
                            "Este dato es obligatorio para una compra.",
                        )
                    )
            if normalized["donation_support_type"]:
                errors.append(
                    RowError(
                        row,
                        "donation_support_type",
                        "No corresponde a una compra.",
                    )
                )
        elif source == "donation":
            if not normalized["donation_support_type"]:
                errors.append(
                    RowError(
                        row,
                        "donation_support_type",
                        "El tipo de respaldo es obligatorio para una donación.",
                    )
                )
            for field in ("supplier", "invoice_total"):
                if normalized[field]:
                    errors.append(
                        RowError(row, field, "No corresponde a una donación.")
                    )

    has_date = bool(normalized["acquired_on"])
    has_reason = bool(normalized["date_unknown_reason"])
    if has_date == has_reason:
        errors.append(
            RowError(
                row,
                "acquired_on",
                "Indica acquired_on o date_unknown_reason, exactamente uno.",
            )
        )

    return normalized, errors


def _validate_license_lot(values, row):
    errors = []
    normalized = {
        "row_number": row,
        "product_name": _text(
            values, "product_name", errors, row, maximum=160
        ),
        "vendor": _text(values, "vendor", errors, row, maximum=160),
        "license_model": _choice(
            values, "license_model", errors, row, LICENSE_MODEL_VALUES
        ),
        "purchased_quantity": _integer(
            values, "purchased_quantity", errors, row
        ),
        "in_use_quantity": _integer(values, "in_use_quantity", errors, row),
        "starts_on": _date(values, "starts_on", errors, row),
        "ends_on": _date(values, "ends_on", errors, row, required=False),
    }
    purchased = normalized["purchased_quantity"]
    in_use = normalized["in_use_quantity"]
    if purchased is not None and in_use is not None and in_use > purchased:
        errors.append(
            RowError(
                row,
                "in_use_quantity",
                "La cantidad en uso no puede superar la comprada.",
            )
        )
    starts_on = normalized["starts_on"]
    ends_on = normalized["ends_on"]
    if starts_on and ends_on and ends_on < starts_on:
        errors.append(
            RowError(row, "ends_on", "La fecha de fin no puede ser anterior al inicio.")
        )
    return normalized, errors


def _add_document_group_errors(rows, errors):
    groups = {}
    for row in rows:
        key = row.get("document_key")
        if key:
            groups.setdefault(key, []).append(row)
    for group in groups.values():
        if len(group) < 2:
            continue
        signatures = {
            tuple(row.get(field) or "" for field in ASSET_DOCUMENT_METADATA)
            for row in group
        }
        if len(signatures) > 1:
            for row in group:
                errors.append(
                    RowError(
                        row["row_number"],
                        "document_key",
                        "Las filas con la misma document_key deben compartir los metadatos del documento.",
                    )
                )


def _add_identity_errors(rows, errors):
    seen = {}
    for row in rows:
        if not all(row.get(field) for field in ("brand", "model", "serial_number")):
            continue
        identity = (
            row["brand"].casefold(),
            row["model"].casefold(),
            row["serial_number"].casefold(),
        )
        previous = seen.get(identity)
        if previous is None:
            seen[identity] = row
            continue
        errors.append(
            RowError(
                row["row_number"],
                "serial_number",
                "Marca, modelo y serie se repiten dentro del archivo.",
            )
        )
        errors.append(
            RowError(
                previous["row_number"],
                "serial_number",
                "Marca, modelo y serie se repiten dentro del archivo.",
            )
        )


def _header_error(expected, header):
    missing = [field for field in expected if field not in header]
    extra = [field for field in header if field not in expected]
    parts = ["Las cabeceras no corresponden a la plantilla."]
    if missing:
        parts.append("Faltan: " + ", ".join(missing) + ".")
    if extra:
        parts.append("Sobran: " + ", ".join(extra) + ".")
    return RowError(1, "header", " ".join(parts))


def parse_import(*, kind, content, schema_version, max_bytes, max_rows):
    if len(content) > max_bytes:
        raise ImportLimitExceeded(
            f"El archivo supera el límite de {max_bytes} bytes."
        )
    if schema_version != SCHEMA_VERSION:
        error = RowError(1, "schema_version", "La versión de plantilla no es válida.")
        return _preview(kind, schema_version, [], [error])

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        error = RowError(1, "file", "El archivo debe estar codificado en UTF-8.")
        return _preview(kind, schema_version, [], [error])

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
    except csv.Error as exc:
        error = RowError(1, "file", f"No se pudo leer el CSV: {exc}.")
        return _preview(kind, schema_version, [], [error])

    expected = fields_for_kind(kind)
    if header is None:
        error = RowError(1, "file", "El archivo está vacío.")
        return _preview(kind, schema_version, [], [error])
    header = [value.strip() for value in header]
    if header != list(expected):
        return _preview(kind, schema_version, [], [_header_error(expected, header)])

    raw_rows = []
    try:
        for raw in reader:
            raw_rows.append(raw)
    except csv.Error as exc:
        error = RowError(1, "file", f"No se pudo leer el CSV: {exc}.")
        return _preview(kind, schema_version, [], [error])

    if len(raw_rows) > max_rows:
        raise ImportLimitExceeded(
            f"El archivo supera el límite de {max_rows} filas."
        )
    if not raw_rows:
        error = RowError(1, "file", "El archivo no contiene filas de datos.")
        return _preview(kind, schema_version, [], [error])

    rows = []
    errors = []
    for offset, raw in enumerate(raw_rows, start=2):
        if not any(cell.strip() for cell in raw):
            errors.append(RowError(offset, "row", "La fila está vacía."))
            continue
        if len(raw) != len(header):
            errors.append(
                RowError(
                    offset,
                    "row",
                    f"La fila tiene {len(raw)} columnas; se esperaban {len(header)}.",
                )
            )
            continue
        values = {field: raw[index] for index, field in enumerate(header)}
        if kind == KIND_ASSETS:
            normalized, row_errors = _validate_asset(values, offset)
        elif kind == KIND_LICENSE_LOTS:
            normalized, row_errors = _validate_license_lot(values, offset)
        else:
            raise ValueError("Tipo de importación no soportado.")
        rows.append(normalized)
        errors.extend(row_errors)

    if kind == KIND_ASSETS:
        _add_document_group_errors(rows, errors)
        _add_identity_errors(rows, errors)

    return _preview(kind, schema_version, rows, errors)
