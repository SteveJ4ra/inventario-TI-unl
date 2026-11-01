# Modelo de datos: fichas y adquisición

## Faculty

- id estable; name obligatorio y único normalizado; active.
- Los activos y revisores referencian Faculty.
- Una facultad referenciada no se borra físicamente.

## AcquisitionDocument

- id; source: PURCHASE o DONATION; reference; document_date; supplier (solo compra); invoice_total (solo compra); support_description/reference (donación); created_by; created_at.
- PURCHASE requiere referencia, fecha, proveedor y total USD.
- DONATION requiere referencia textual de respaldo.
- No contiene binario ni imagen.

## AcquisitionLine

- document; asset; item_value USD.
- Para PURCHASE item_value es importe por equipo en la factura.
- Para DONATION item_value es valor estimado individual.
- Un documento puede asociarse a muchos activos; un activo tiene un registro de adquisición vigente.
- Cambios quedan auditados; la política de revisión de documento existente es apéndice de la auditoría.

## Asset metadata audit

- asset, actor, created_at, reason, before_json, after_json.
- Solo campos descriptivos y faculty_id.
- No reemplaza movimientos de condición, asignación, custodio o ubicación.

## Custodian profile audit

- custodian, actor, created_at, before_json, after_json.
- Movimientos antiguos consultan snapshot inmutable de nombre/correo del momento del movimiento.

## Asset acquisition date

- acquired_on nullable solamente si date_unknown_reason está presente.
- Moneda USD se centraliza en configuración del backend; persistir importes en decimal, sin formato localizado en DB.
## Auditoría de facultad responsable

`AssetFacultyChange`: activo, facultad anterior/nueva, motivo obligatorio, operador autor y fecha/hora del servidor. El cambio se realiza con bloqueo transaccional del activo. La integración 005 impide el cambio mientras una solicitud de baja esté pendiente.
