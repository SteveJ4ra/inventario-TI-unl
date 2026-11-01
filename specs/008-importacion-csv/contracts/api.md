# Contrato API: CSV

Rutas bajo `/api/imports/`, solo Gestores y protección CSRF de 002.

- `POST /api/imports/previews` multipart: `kind=assets|license_lots`, `file`, `schema_version`; retorna `batch_id`, resumen, errores por fila/campo y estado. No escribe registros de dominio.
- `POST /api/imports/{batch_id}/confirm`: primera confirmación explícita; exige estado PREVIEW_READY, hash vigente y que la sesión corresponda al Gestor que cargó el lote.
- `POST /api/imports/{batch_id}/apply`: confirmación final; exige CONFIRMED_ONCE, mismo Gestor que cargó y confirmó/hash y aplica transacción atómica.
- `GET /api/imports/{batch_id}`: estado y vista previa/resumen al actor autorizado.
- `POST /api/imports/{batch_id}/cancel`: cancelar preview sin crear datos.

Errores: 400 formato/esquema/campos; 401 sesión; 403 permiso/propietario; 404 lote; 409 lote vencido, ya aplicado o estado conflictivo; 413 límites técnicos excedidos. Reintentar `apply` de un lote aplicado retorna resultado existente sin duplicar.
