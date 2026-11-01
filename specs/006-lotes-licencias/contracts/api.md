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