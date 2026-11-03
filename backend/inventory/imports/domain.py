"""Parser y validación local de las plantillas CSV de 008.

Sin Django ni ORM: valida forma, tipos, campos condicionales, documentos
compartidos y duplicados dentro del archivo. Las referencias contra la base de
datos se comprueban mediante los gateways de las features 003/006.
"""

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from . import schemas

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
INTEGER_PATTERN = re.compile(r"^\d+$")
MAX_MONEY = Decimal("9999999999.99")


class CsvLimitExceeded(Exception):
    """El archivo o el número de filas supera el límite técnico configurado."""


class UnsupportedSchema(ValueError):
    """Tipo o versión de plantilla no soportada."""


@dataclass
class ParseResult:
    kind: str
    schema_version: str
    header: list
    rows: list
    errors: list
    summary: dict
    content_hash: str


def _error(errors, row, field, message):
    errors.append({"row": row, "field": field, "message": message})


def _text(value):
    return (value or "").strip()


def _money(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount < 0 or amount > MAX_MONEY:
        return None
    if amount != amount.quantize(Decimal("0.01")):
        return None
    return amount.quantize(Decimal("0.01"))


def _date(value):
    if not DATE_PATTERN.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _integer(value):
    if not INTEGER_PATTERN.fullmatch(value):
        return None
    return int(value)


def _required(values, name, label, errors, row, maximum=None):
    value = _text(values.get(name))
    if not value:
        _error(errors, row, name, f"{label} es obligatorio.")
    elif maximum is not None and len(value) > maximum:
        _error(errors, row, name, f"{label} admite como máximo {maximum} caracteres.")
    return value


def _optional(values, name, label, errors, row, maximum=None):
    value = _text(values.get(name))
    if maximum is not None and len(value) > maximum:
        _error(errors, row, name, f"{label} admite como máximo {maximum} caracteres.")
    return value


def _int_field(value, name, label, errors, row, required=True):
    if not value:
        if required:
            _error(errors, row, name, f"{label} es obligatorio.")
        return None
    parsed = _integer(value)
    if parsed is None:
        _error(errors, row, name, f"{label} debe ser un entero no negativo.")
    return parsed


def _decimal_field(value, name, label, errors, row, required=True):
    if not value:
        if required:
            _error(errors, row, name, f"{label} es obligatorio.")
        return None
    parsed = _money(value)
    if parsed is None:
        _error(
            errors,
            row,
            name,
            f"{label} debe ser un importe no negativo con dos decimales como máximo.",
        )
        return None
    return f"{parsed:.2f}"


def _date_field(value, name, label, errors, row, required=True):
    if not value:
        if required:
            _error(errors, row, name, f"{label} es obligatorio.")
        return None
    parsed = _date(value)
    if parsed is None:
        _error(errors, row, name, f"{label} debe usar el formato AAAA-MM-DD.")
        return None
    return parsed.isoformat()


def _validate_asset(values, row, errors, identities, documents):
    name = _required(values, "name", "Nombre", errors, row, 160)
    description = _required(values, "description", "Descripción", errors, row, 2000)
    category = _text(values.get("category")).lower()
    if category not in schemas.CATEGORIES:
        _error(errors, row, "category", "Categoría no reconocida.")
    brand = _required(values, "brand", "Marca", errors, row, 120)
    model = _required(values, "model", "Modelo", errors, row, 120)
    serial = _required(values, "serial_number", "Número de serie", errors, row, 160)
    location = _required(values, "location", "Ubicación", errors, row, 240)
    condition = _text(values.get("condition")).lower()
    if condition not in schemas.CONDITIONS:
        _error(errors, row, "condition", "Condición no reconocida.")

    faculty_id = _int_field(
        _text(values.get("faculty_id")), "faculty_id", "faculty_id", errors, row
    )
    if faculty_id is not None and faculty_id < 1:
        _error(errors, row, "faculty_id", "faculty_id debe ser mayor que cero.")

    document_id_raw = _text(values.get("acquisition_document_id"))
    document_id = (
        _int_field(
            document_id_raw,
            "acquisition_document_id",
            "acquisition_document_id",
            errors,
            row,
        )
        if document_id_raw
        else None
    )
    if document_id is not None and document_id < 1:
        _error(
            errors,
            row,
            "acquisition_document_id",
            "acquisition_document_id debe ser mayor que cero.",
        )
    document_key = _optional(
        values, "document_key", "document_key", errors, row, maximum=80
    )
    if document_key and not KEY_PATTERN.fullmatch(document_key):
        _error(
            errors,
            row,
            "document_key",
            "document_key solo admite letras, números, punto, guion y guion bajo.",
        )

    if document_id and document_key:
        _error(
            errors,
            row,
            "document_key",
            "Usa acquisition_document_id o document_key, nunca ambos.",
        )
    if not document_id and not document_key:
        _error(
            errors,
            row,
            "acquisition_document_id",
            "Indica un documento existente o una document_key local.",
        )

    source_raw = _text(values.get("document_source")).lower()
    source = schemas.DOCUMENT_SOURCES.get(source_raw)
    reference = _optional(
        values, "document_reference", "document_reference", errors, row, 160
    )
    supplier = _optional(values, "supplier", "supplier", errors, row, 160)
    support = _optional(
        values, "support_description", "support_description", errors, row, 500
    )
    document_date = _date_field(
        _text(values.get("document_date")),
        "document_date",
        "document_date",
        errors,
        row,
        required=False,
    )
    invoice_total = _decimal_field(
        _text(values.get("invoice_total")),
        "invoice_total",
        "invoice_total",
        errors,
        row,
        required=False,
    )

    if document_id:
        if any(
            [
                document_key,
                source_raw,
                reference,
                supplier,
                support,
                document_date,
                invoice_total,
            ]
        ):
            _error(
                errors,
                row,
                "acquisition_document_id",
                "Con un documento existente deja vacíos los metadatos del documento nuevo.",
            )
    elif document_key:
        if source is None:
            _error(
                errors,
                row,
                "document_source",
                "document_source debe ser compra o donacion.",
            )
        if not reference:
            _error(
                errors,
                row,
                "document_reference",
                "document_reference es obligatorio para un documento nuevo.",
            )
        if source == "PURCHASE":
            if not document_date:
                _error(
                    errors,
                    row,
                    "document_date",
                    "La fecha del documento es obligatoria en compras.",
                )
            if not supplier:
                _error(errors, row, "supplier", "El proveedor es obligatorio en compras.")
            if not invoice_total:
                _error(
                    errors,
                    row,
                    "invoice_total",
                    "El total de la factura es obligatorio en compras.",
                )
            if support:
                _error(
                    errors,
                    row,
                    "support_description",
                    "Déjalo vacío para compras; usa document_reference.",
                )
        elif source == "DONATION":
            if not support:
                _error(
                    errors,
                    row,
                    "support_description",
                    "La descripción del respaldo es obligatoria en donaciones.",
                )
            if supplier or invoice_total:
                _error(
                    errors,
                    row,
                    "supplier",
                    "Una donación no admite proveedor ni total de factura.",
                )
        metadata = (source, reference, document_date, supplier, invoice_total, support)
        if document_key in documents and documents[document_key] != metadata:
            _error(
                errors,
                row,
                "document_key",
                "Los metadatos no coinciden con otras filas de la misma document_key.",
            )
        documents.setdefault(document_key, metadata)

    item_value = _decimal_field(
        _text(values.get("item_value")), "item_value", "item_value", errors, row
    )
    acquired_on = _date_field(
        _text(values.get("acquired_on")),
        "acquired_on",
        "acquired_on",
        errors,
        row,
        required=False,
    )
    reason = _optional(
        values,
        "date_unknown_reason",
        "date_unknown_reason",
        errors,
        row,
        maximum=500,
    )
    if acquired_on and reason:
        _error(
            errors,
            row,
            "date_unknown_reason",
            "Indica la fecha o el motivo de fecha desconocida, no ambos.",
        )
    if not acquired_on and not reason:
        _error(
            errors,
            row,
            "acquired_on",
            "Indica acquired_on o date_unknown_reason.",
        )

    if brand and model and serial:
        identity = (brand.lower(), model.lower(), serial.lower())
        if identity in identities:
            _error(
                errors,
                row,
                "serial_number",
                "Marca, modelo y número de serie se repiten dentro del archivo.",
            )
        identities.add(identity)

    return {
        "name": name,
        "description": description,
        "category": category or None,
        "brand": brand,
        "model": model,
        "serial_number": serial,
        "location": location,
        "condition": condition or None,
        "faculty_id": faculty_id,
        "acquisition_document_id": document_id,
        "document_key": document_key or None,
        "document_source": source,
        "document_reference": reference,
        "document_date": document_date,
        "supplier": supplier,
        "invoice_total": invoice_total,
        "support_description": support,
        "item_value": item_value,
        "acquired_on": acquired_on,
        "date_unknown_reason": reason,
    }


def _validate_license_lot(values, row, errors):
    product = _required(
        values, "product_name", "Nombre del producto", errors, row, 160
    )
    vendor = _required(values, "vendor", "Proveedor", errors, row, 160)
    license_model = _text(values.get("license_model")).upper()
    if license_model not in schemas.LICENSE_MODELS:
        _error(
            errors,
            row,
            "license_model",
            "license_model debe ser USER_SEAT o DEVICE_SEAT.",
        )
    purchased = _int_field(
        _text(values.get("purchased_quantity")),
        "purchased_quantity",
        "Cantidad comprada",
        errors,
        row,
    )
    in_use = _int_field(
        _text(values.get("in_use_quantity")),
        "in_use_quantity",
        "Cantidad en uso",
        errors,
        row,
    )
    if purchased is not None and in_use is not None and in_use > purchased:
        _error(
            errors,
            row,
            "in_use_quantity",
            "La cantidad en uso no puede superar la comprada.",
        )
    starts_on = _date_field(
        _text(values.get("starts_on")),
        "starts_on",
        "Fecha de inicio",
        errors,
        row,
    )
    ends_on = _date_field(
        _text(values.get("ends_on")),
        "ends_on",
        "Fecha de fin",
        errors,
        row,
        required=False,
    )
    if starts_on and ends_on and ends_on < starts_on:
        _error(
            errors,
            row,
            "ends_on",
            "La fecha de fin no puede ser anterior a la de inicio.",
        )
    return {
        "product_name": product,
        "vendor": vendor,
        "license_model": license_model or None,
        "purchased_quantity": purchased,
        "in_use_quantity": in_use,
        "starts_on": starts_on,
        "ends_on": ends_on,
    }


def summarize(kind, rows):
    valid = [row["values"] for row in rows if row["valid"]]
    summary = {"record_count": len(valid), "total_rows": len(rows)}
    if kind == schemas.ASSETS:
        summary["new_documents"] = len(
            {value["document_key"] for value in valid if value["document_key"]}
        )
        summary["existing_documents"] = len(
            {
                value["acquisition_document_id"]
                for value in valid
                if value["acquisition_document_id"]
            }
        )
    else:
        summary["purchased_total"] = sum(
            value["purchased_quantity"] or 0 for value in valid
        )
        summary["in_use_total"] = sum(value["in_use_quantity"] or 0 for value in valid)
    return summary


def content_hash(kind, schema_version, rows, summary):
    payload = {
        "kind": kind,
        "schema_version": schema_version,
        "rows": [{"row": row["row"], "values": row["values"]} for row in rows],
        "summary": summary,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _empty_result(kind, schema_version, header, errors):
    rows = []
    summary = {"record_count": 0, "total_rows": 0}
    return ParseResult(
        kind=kind,
        schema_version=schema_version,
        header=header,
        rows=rows,
        errors=errors,
        summary=summary,
        content_hash=content_hash(kind, schema_version, rows, summary),
    )


def parse_csv(kind, schema_version, raw, max_bytes, max_rows):
    if kind not in schemas.KINDS or schema_version != schemas.default_version(kind):
        raise UnsupportedSchema("Tipo o versión de plantilla no soportada.")
    if len(raw) > max_bytes:
        raise CsvLimitExceeded("El archivo supera el tamaño máximo permitido.")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _empty_result(
            kind,
            schema_version,
            [],
            [
                {
                    "row": None,
                    "field": "",
                    "message": "El archivo no está codificado en UTF-8.",
                }
            ],
        )
    if "\x00" in text:
        return _empty_result(
            kind,
            schema_version,
            [],
            [
                {
                    "row": None,
                    "field": "",
                    "message": "El archivo contiene bytes nulos no permitidos.",
                }
            ],
        )

    expected = schemas.columns(kind)
    try:
        reader = csv.reader(io.StringIO(text, newline=""))
        try:
            header = next(reader)
        except StopIteration:
            return _empty_result(
                kind,
                schema_version,
                [],
                [
                    {
                        "row": None,
                        "field": "",
                        "message": "El archivo está vacío; falta la cabecera.",
                    }
                ],
            )
        normalized = [cell.strip().lower() for cell in header]
        errors = []
        if len(set(normalized)) != len(normalized):
            errors.append(
                {
                    "row": 1,
                    "field": "",
                    "message": "La cabecera repite nombres de columna.",
                }
            )
        for name in expected:
            if name not in normalized:
                errors.append(
                    {
                        "row": 1,
                        "field": name,
                        "message": f"Falta la columna {name}.",
                    }
                )
        for name in normalized:
            if name not in expected:
                errors.append(
                    {
                        "row": 1,
                        "field": name,
                        "message": f"Columna no permitida: {name}.",
                    }
                )
        if errors:
            return _empty_result(kind, schema_version, normalized, errors)

        rows = []
        data_errors = []
        identities = set()
        documents = {}
        previous_line = reader.line_num
        try:
            for record in reader:
                row_number = previous_line + 1
                previous_line = reader.line_num
                if not any(cell.strip() for cell in record):
                    continue
                if len(rows) >= max_rows:
                    raise CsvLimitExceeded(
                        "El archivo supera el número máximo de filas permitido."
                    )
                if len(record) != len(normalized):
                    _error(
                        data_errors,
                        row_number,
                        "",
                        f"La fila tiene {len(record)} columnas; se esperaban {len(normalized)}.",
                    )
                    rows.append(
                        {
                            "row": row_number,
                            "values": {name: None for name in normalized},
                            "valid": False,
                        }
                    )
                    continue
                values = dict(zip(normalized, record))
                before = len(data_errors)
                if kind == schemas.ASSETS:
                    canonical = _validate_asset(
                        values, row_number, data_errors, identities, documents
                    )
                else:
                    canonical = _validate_license_lot(
                        values, row_number, data_errors
                    )
                rows.append(
                    {
                        "row": row_number,
                        "values": canonical,
                        "valid": len(data_errors) == before,
                    }
                )
        except csv.Error as exc:
            data_errors.append(
                {
                    "row": reader.line_num,
                    "field": "",
                    "message": f"CSV mal formado: {exc}.",
                }
            )
    except csv.Error as exc:
        return _empty_result(
            kind,
            schema_version,
            [],
            [
                {
                    "row": None,
                    "field": "",
                    "message": f"CSV mal formado: {exc}.",
                }
            ],
        )

    if not rows:
        data_errors.append(
            {
                "row": None,
                "field": "",
                "message": "El archivo no contiene filas de datos.",
            }
        )
    summary = summarize(kind, rows)
    return ParseResult(
        kind=kind,
        schema_version=schema_version,
        header=normalized,
        rows=rows,
        errors=data_errors,
        summary=summary,
        content_hash=content_hash(kind, schema_version, rows, summary),
    )
