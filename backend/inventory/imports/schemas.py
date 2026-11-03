"""Plantillas CSV versionadas de 008.

Este módulo no importa Django: las pruebas aisladas pueden validar los
esquemas y el parser sin registrar modelos ni depender de 003/006.
"""

from pathlib import Path

ASSETS = "assets"
LICENSE_LOTS = "license_lots"
KINDS = (ASSETS, LICENSE_LOTS)

KIND_LABELS = {
    ASSETS: "Activos",
    LICENSE_LOTS: "Lotes de licencias",
}

SCHEMA_VERSIONS = {
    ASSETS: "assets-v1",
    LICENSE_LOTS: "license-lots-v1",
}

ASSET_COLUMNS = [
    "name",
    "description",
    "category",
    "brand",
    "model",
    "serial_number",
    "location",
    "condition",
    "faculty_id",
    "acquisition_document_id",
    "document_key",
    "document_source",
    "document_reference",
    "document_date",
    "supplier",
    "invoice_total",
    "support_description",
    "item_value",
    "acquired_on",
    "date_unknown_reason",
]

LICENSE_LOT_COLUMNS = [
    "product_name",
    "vendor",
    "license_model",
    "purchased_quantity",
    "in_use_quantity",
    "starts_on",
    "ends_on",
]

COLUMNS = {
    ASSETS: ASSET_COLUMNS,
    LICENSE_LOTS: LICENSE_LOT_COLUMNS,
}

CATEGORIES = {
    "computadora_escritorio",
    "portatil",
    "monitor",
    "impresora",
    "equipo_red",
    "periferico",
}

CONDITIONS = {"operativo", "averiado", "en_reparacion"}

LICENSE_MODELS = {"USER_SEAT", "DEVICE_SEAT"}

DOCUMENT_SOURCES = {
    "compra": "PURCHASE",
    "purchase": "PURCHASE",
    "donacion": "DONATION",
    "donación": "DONATION",
    "donation": "DONATION",
}

DATOS = Path(__file__).resolve().parent
TEMPLATE_FILES = {
    kind: DATOS / "templates" / f"{SCHEMA_VERSIONS[kind]}.csv" for kind in KINDS
}
EXAMPLE_FILES = {
    kind: DATOS / "examples" / f"{SCHEMA_VERSIONS[kind]}.example.csv" for kind in KINDS
}


def columns(kind):
    try:
        return COLUMNS[kind]
    except KeyError:
        raise ValueError("Tipo de importación no soportado.") from None


def default_version(kind):
    try:
        return SCHEMA_VERSIONS[kind]
    except KeyError:
        raise ValueError("Tipo de importación no soportado.") from None
