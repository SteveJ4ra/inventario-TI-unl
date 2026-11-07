# Modelo de datos: lotes de licencias

## SoftwareLicenseLot

- id; product_name; vendor; license_model USER_SEAT o DEVICE_SEAT.
- purchased_quantity >= 0; in_use_quantity entre 0 y purchased_quantity.
- starts_on requerido; ends_on nullable y no anterior a starts_on.
- created_by, created_at, revision.
- remaining_quantity = purchased_quantity - in_use_quantity; se calcula.
- temporal_status derivado en lectura: NOT_STARTED, CURRENT, EXPIRED.
- No contiene activation_key, custodian, asset_id ni invoice_id.

## LicenseLotAudit

- lot; actor; timestamp; before_json; after_json.
- Toda modificación conserva auditoría.
- Sin borrado automático.

## Implementación y restricciones

Los textos de producto/proveedor admiten hasta 160 caracteres. Cantidades: PositiveIntegerField (0–2147483647). Fechas se guardan como date; revision es PositiveBigIntegerField, inicia en 0 y la asigna el servicio.

LicenseLotAudit incluye además actor_label (snapshot del nombre, máximo 150) y resulting_revision, único por lote. FK a lote y autores con PROTECT. Se registra el alta con before_json={} y luego cada edición efectiva. El servicio actualiza la proyección y agrega evidencia en una sola transacción; el historial tiene guardas ORM y trigger contra UPDATE/DELETE. No hay cascada que borre evidencia.

Migraciones: 0003_importbatch → 0004_license_lots → 0005_license_lot_audit_immutable. No se cambian migraciones antiguas ni datos de 002. Los nombres y orden son los existentes al implementar; una colisión futura de ramas requiere revisión normal del grafo, sin renombrar migraciones ya aplicadas.
