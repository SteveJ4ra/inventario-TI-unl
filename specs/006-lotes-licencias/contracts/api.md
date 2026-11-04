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

## Detalles implementados de 006

JSON UTF-8 únicamente en escrituras; máximo 16 KiB de cuerpo. Campos desconocidos o reservados se rechazan con 400; otros tipos de contenido con 415. Los rechazos no crean lotes ni auditorías. Se conservan errores `{code, detail, fields?}` de 002. Todas las respuestas de estas rutas llevan `Cache-Control: no-store`.

### Entradas

- `product_name` y `vendor`: texto obligatorio, trim exterior, máximo 160 caracteres, no vacío.
- `license_model`: `USER_SEAT` o `DEVICE_SEAT`.
- `purchased_quantity` e `in_use_quantity`: números JSON enteros de 0 a 2147483647; sin booleanos, fracciones ni cadenas numéricas. El límite corresponde al tipo integer PostgreSQL, no a un mínimo de compra.
- `starts_on`: fecha ISO `YYYY-MM-DD` obligatoria.
- `ends_on`: fecha ISO o null; omitirla en POST equivale a null.
- PATCH acepta cualquier subconjunto de los siete campos, y exige `expected_revision` entero no negativo (máximo 9223372036854775806). Se valida el resultado fusionado con el lote actual. Omitir `ends_on` conserva su valor; enviarlo null elimina la fecha final.
- PATCH vacío, sin campos editables o sin cambio real devuelve 400 sin incrementar revisión. Una petición válida con revisión obsoleta devuelve 409 `stale_revision`; no se reenvía automáticamente.

No se reciben id, revision resultante, created_by/created_at, actor, timestamp, before/after, estado, remanentes, claves, custodian, asset_id ni invoice_id. El historial es solo lectura. No se ofrecen PUT, DELETE ni edición de eventos.

### Consultas y paginación

GET lista admite solo `page` (entero 1–2147483647, predeterminado 1), `search` (hasta 240 caracteres, producto/proveedor con coincidencia parcial sin distinguir mayúsculas), `license_model` y `temporal_status` (`NOT_STARTED`, `CURRENT`, `EXPIRED`). Los filtros se combinan con AND. Parámetros/enums/páginas inválidos devuelven 400. Historial acepta solo `page`.

Lista e historial devuelven `{count, next, previous, results}`, hasta 50 registros por página. Lista ordenada por id descendente; historial por resulting_revision e id descendentes. Página 1 sin datos es válida; una página posterior inexistente devuelve 400. Los enlaces conservan filtros. El filtro y las etiquetas de cada respuesta usan el mismo día local del servidor. La configuración actual es `TIME_ZONE=UTC`; `timezone.localdate()` respeta la zona activa. Las fechas de calendario no se convierten a timestamps ni se les resta horas en el navegador.

### Salida y auditoría

POST devuelve 201; detalle/PATCH devuelven 200 con:

```json
{"id":1,"product_name":"Suite de prueba","vendor":"Proveedor","license_model":"USER_SEAT","purchased_quantity":10,"in_use_quantity":4,"remaining_quantity":6,"starts_on":"2026-01-01","ends_on":null,"temporal_status":"CURRENT","revision":0,"created_at":"2026-01-01T12:00:00Z","created_by":{"id":1,"username":"gestor"}}
```

El ejemplo de CURRENT corresponde a una consulta posterior al inicio. El estado siempre se calcula al consultar.

Alta crea auditoría revisión 0 con before_json vacío; cada edición efectiva crea una nueva fila y aumenta revisión en 1. Evento: `{id, lot_id, actor: {id, username, recorded_label}, timestamp, before_json, after_json, resulting_revision}`. Los snapshots incluyen los siete campos editables más revision; recorded_label conserva el nombre registrado aunque se renombre la cuenta. UPDATE/DELETE del historial se rechaza también por trigger PostgreSQL.

Gestores activos tienen igual acceso a todos los lotes, incluso los creados por otro gestor. Usuarios anónimos, inactivos, sin Gestores o superusuarios sin ese grupo reciben 403. Escrituras por sesión requieren CSRF; origen ajeno es rechazado. El servidor define autoría, tiempos y revisión resultante.

### Contrato proveedor para 008

`inventory.license_services.validate_license_lot(data)` valida valores canónicos sin escribir; devuelve datos validados o ValidationError con errores por campo. `import_license_lots(actor=..., rows=[valores...])` exige Gestor y crea todo en una transacción, devolviendo `{kind: "license_lots", created: N}`. Participa en la transacción exterior de 008. El gateway existente delega la validación a 006. No se agregó procesamiento CSV a este paquete.
