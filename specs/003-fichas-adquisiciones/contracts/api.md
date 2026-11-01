# Contratos API: fichas y adquisición

Todos los endpoints requieren sesión autenticada según rol. Las mutaciones usan CSRF. Campos desconocidos o reservados se rechazan.

| Método y ruta | Actor | Resultado |
|---|---|---|
| GET /api/faculties/ | Gestor / operador | Lista activa de facultades |
| POST /api/operator/faculties/ | Operador | Añade facultad |
| PATCH /api/operator/faculties/{id}/ | Operador | Corrige nombre/estado sin borrar referencias |
| POST /api/acquisitions/ | Gestor | Crea documento PURCHASE o DONATION y sus líneas |
| GET /api/acquisitions/{id}/ | Gestor | Documento común y activos/importes enlazados |
| PATCH /api/acquisitions/{id}/ | Gestor | Corrige datos con motivo y auditoría |
| PATCH /api/assets/{id}/ | Gestor | Edita solo campos descriptivos y adquisición con reason obligatorio; facultad se rechaza como campo reservado |
| PATCH /api/operator/assets/{id}/faculty/ | Operador | Cambia facultad con motivo e historial; 409 si hay solicitud de baja pendiente (regla completada en 005) |
| PATCH /api/custodians/{id}/ | Gestor | Edita nombre/correo/dependencia, preservando snapshots |
| GET /api/assets/{id}/history/ | Gestor | Orden cronológico combinado de movimientos y cambios de ficha |

Purchase request: reference, document_date, supplier, invoice_total, items[{asset_id, item_value}].
Donation request: reference, support_type, items[{asset_id, estimated_value}].
Asset date: acquired_on o date_unknown_reason; exactamente una alternativa válida.
Asset edit: reason y solo campos descriptivos/adquisición; facultad y cambios de estado se rechazan en esta ruta. Faculty change usa ruta de operador, reason y before/after audit.
Currency: respuesta monetaria incluye currency=USD; cliente no puede elegir otra moneda.

Errores: 400 validación, 403 acceso, 404 inexistente, 409 duplicado/conflicto; sin cambios parciales ante error.

## Extensión de alta y acceso

POST `/api/acquisitions/` admite metadatos del documento con `items` omitido/vacío; items, si se aportan, solo enlaza activos existentes. POST `/api/assets/` mantiene los campos de 002 y exige `faculty_id`, `acquisition_document_id`, `item_value` y exactamente una alternativa `acquired_on`/`date_unknown_reason`. El documento y la facultad deben existir; tipo del documento determina valor de compra o estimado. Activo y línea se guardan juntos o nada.

PATCH de activo/facultad y documento compartido exige `expected_revision` (documentos: revisiones de todos los activos afectados). La facultad inicial la indica el Gestor al registrar; cualquier cambio posterior solo se hace por la ruta de Operador. Se implementan provisión y sesión de Operador en este incremento, según contratos transversales.
