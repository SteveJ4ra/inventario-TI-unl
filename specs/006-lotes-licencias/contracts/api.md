# Contratos API: licencias

| Método/ruta | Permiso | Resultado |
|---|---|---|
| GET /api/license-lots/ | Gestor | Lista paginada, busca por producto/proveedor y filtra por tipo/estado |
| POST /api/license-lots/ | Gestor | Crea lote, fecha inicial requerida |
| GET /api/license-lots/{id}/ | Gestor | Detalle, compradas, en uso, remanentes y estado temporal |
| PATCH /api/license-lots/{id}/ | Gestor | Edita campos/cantidades con revision y auditoría |
| GET /api/license-lots/{id}/history/ | Gestor | Auditoría de cambios |

POST/PATCH valida in_use_quantity <= purchased_quantity. Fecha fin puede ser null. Estado no se acepta como campo de entrada; se calcula.
Una fecha de inicio futura produce NOT_STARTED; una fecha de fin anterior a hoy produce EXPIRED. El lote vencido conserva remaining_quantity.
Errores JSON consistentes con 002: 400/403/404/409; actualización obsoleta devuelve 409.

Campos canónicos: product_name, vendor, license_model (USER_SEAT/DEVICE_SEAT), purchased_quantity, in_use_quantity, starts_on y ends_on. Cantidades enteras no negativas, conforme a FR-003; ends_on >= starts_on si existe. Día fin inclusivo: estado EXPIRED solo al día siguiente, calculado con fecha local del servidor configurado. PATCH recibe expected_revision y devuelve revision; estado y remaining_quantity son solo salida.
