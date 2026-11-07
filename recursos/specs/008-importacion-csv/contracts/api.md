# Contrato API: CSV

Rutas bajo `/api/imports/`, solo Gestores y protección CSRF de 002.

- `POST /api/imports/previews` multipart: `kind=assets|license_lots`, `file`, `schema_version`; retorna `batch_id`, resumen, errores por fila/campo y estado. No escribe registros de dominio.
- `POST /api/imports/{batch_id}/confirm`: primera confirmación explícita; exige estado PREVIEW_READY, hash vigente y que la sesión corresponda al Gestor que cargó el lote.
- `POST /api/imports/{batch_id}/apply`: confirmación final; exige CONFIRMED_ONCE, mismo Gestor que cargó y confirmó/hash y aplica transacción atómica.
- `GET /api/imports/{batch_id}`: estado y vista previa/resumen al actor autorizado.
- `POST /api/imports/{batch_id}/cancel`: cancelar preview sin crear datos.

Errores: 400 formato/esquema/campos; 403 sesión; 403 permiso/propietario; 404 lote; 409 lote vencido, cancelado, no confirmado o estado conflictivo; 413 límites técnicos excedidos. Reintentar `apply` de un lote aplicado retorna resultado existente sin duplicar.

Primera aplicación: 201. Repetición de APPLIED por su propietario: 200 con resultado anterior, nunca 409 por estar aplicado. Al aplicar bloquear batch y revalidar contra DB actual todas las referencias y unicidad. Preview inválido devuelve 400 con batch_id y errores completos; válido devuelve 201 con PREVIEW_READY. La consulta GET permite paginar todas las filas validadas, incluidas sus versiones/hash; no solo un resumen.

La plantilla de activos identifica documento compartido por acquisition_document_id existente o document_key local para un documento nuevo, nunca ambas alternativas. Referencia textual igual no autoriza fusionar documentos de distintos proveedores. Todos los metadatos de la misma document_key deben coincidir; discrepancias invalidan todo el lote.
