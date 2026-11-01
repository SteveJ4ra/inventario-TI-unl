# Modelo de datos: lotes de licencias

## SoftwareLicenseLot

- id; product_name; publisher/vendor; license_model USER_SEAT o DEVICE_SEAT.
- purchased_quantity >= 1; in_use_quantity entre 0 y purchased_quantity.
- starts_on requerido; ends_on nullable y no anterior a starts_on.
- created_by, created_at, updated_revision.
- remaining_quantity = purchased_quantity - in_use_quantity; se calcula.
- temporal_status derivado en lectura: NOT_STARTED, CURRENT, EXPIRED.
- No contiene activation_key, custodian, asset_id ni invoice_id.

## LicenseLotAudit

- lot; actor; timestamp; before_json; after_json.
- Toda modificación conserva auditoría.
- Sin borrado automático.