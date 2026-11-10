from pathlib import Path

KIND_ASSETS = "assets"
KIND_LICENSE_LOTS = "license_lots"
KINDS = (KIND_ASSETS, KIND_LICENSE_LOTS)
SCHEMA_VERSION = "v1"

ASSET_FIELDS = (
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
    "acquisition_source",
    "document_reference",
    "document_date",
    "supplier",
    "invoice_total",
    "donation_support_type",
    "acquired_on",
    "date_unknown_reason",
    "item_value",
)

LICENSE_LOT_FIELDS = (
    "product_name",
    "vendor",
    "license_model",
    "purchased_quantity",
    "in_use_quantity",
    "starts_on",
    "ends_on",
)

CATEGORY_VALUES = {
    "computadora_escritorio",
    "portatil",
    "monitor",
    "impresora",
    "equipo_red",
    "periferico",
}
CONDITION_VALUES = {"operativo", "averiado", "en_reparacion"}
ACQUISITION_SOURCES = {"purchase", "donation"}
LICENSE_MODEL_VALUES = {"USER_SEAT", "DEVICE_SEAT"}

ASSET_DOCUMENT_METADATA = (
    "acquisition_source",
    "document_reference",
    "document_date",
    "supplier",
    "invoice_total",
    "donation_support_type",
)

TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "templates"


def fields_for_kind(kind):
    if kind == KIND_ASSETS:
        return ASSET_FIELDS
    if kind == KIND_LICENSE_LOTS:
        return LICENSE_LOT_FIELDS
    raise ValueError("Tipo de importación no soportado.")


def template_path(kind):
    if kind == KIND_ASSETS:
        return TEMPLATE_DIRECTORY / "assets-v1.csv"
    if kind == KIND_LICENSE_LOTS:
        return TEMPLATE_DIRECTORY / "license-lots-v1.csv"
    raise ValueError("Tipo de importación no soportado.")


def template_bytes(kind):
    return template_path(kind).read_bytes()
