# feat: 008-importacion-csv

## Alcance

Implementa la importación CSV estricta de activos (`assets-v1`) y lotes de licencias (`license-lots-v1`) para gestores:

- Plantillas y ejemplos versionados con BOM UTF-8.
- Parser puro con cabeceras exactas, normalización, errores completos por fila/campo y hash SHA-256 estable.
- Vista previa persistida e inmutable, sin escribir activos/licencias.
- Doble confirmación ligada al hash, expiración de preview, cancelación y propiedad por gestor.
- Aplicación bloqueada por lote, revalidada contra el gateway, idempotente (201 primera vez / 200 reintento) y sin datos parciales.
- UI con descarga de plantilla, carga, errores, todas las filas paginadas, resumen y dos confirmaciones explícitas.

## SDD

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Tareas: [tasks.md](tasks.md)
- Implementación: [implementation.md](implementation.md)
- Validación: [validation.md](validation.md)
- Integración: [integration-notes.md](integration-notes.md)

## FR y tareas

- FR-001 a FR-012 cubiertos en orquestación/UI dentro de lo verificable sin proveedores.
- T001–T003, T005–T006, T008–T014 completadas.
- T004 y T007 permanecen parciales: parser y orquestación listos, pero la reutilización real de validadores y la transacción de dominio dependen de 003/006.

## API y migraciones

Nuevas rutas:

- `GET /api/imports/templates/{kind}/`
- `POST /api/imports/previews/` (multipart, 201 válido / 400 con errores)
- `GET /api/imports/{batch_id}/?page=N`
- `POST /api/imports/{batch_id}/confirm/`
- `POST /api/imports/{batch_id}/apply/` (201 primera aplicación / 200 reintento)
- `POST /api/imports/{batch_id}/cancel/`

Errores: 403 propietario/sesión, 404 inexistente, 409 conflicto/estado/hash, 413 límites, 503 proveedor no integrado.

Migración nueva: `inventory.0003_importbatch`. No modifica migraciones existentes. `makemigrations --check` sin cambios.

## Límites

- 2 MB y 2000 filas por archivo.
- Preview: 24 h (`IMPORT_PREVIEW_TTL_SECONDS=86400`).
- Retención de resultados configurada a 30 días (purga automática pendiente).
- Contenido temporal se elimina al aplicar, cancelar o vencer.

## Pruebas ejecutadas

- `python -m unittest discover -s backend/inventory/isolated_tests/imports -p "test_*.py"`: 16 OK.
- `python backend/tools/test_postgres.py`: 45 OK en PostgreSQL 17 efímero, incluidas concurrencia e idempotencia.
- `npm test -- --run` (frontend): 20 OK.
- `npm run build`: OK.
- `manage.py makemigrations --check --dry-run`: `No changes detected`.

Las pruebas API usan un fake exclusivamente de tests; no son integración real con 003/006.

## Dependencias pendientes

- 003 y 006 no están en `origin/develop`: no existen sus modelos/servicios. El gateway de producción responde 503 y no simula éxito.
- Falta verificar con proveedores reales: atomicidad de dominio, unicidad concurrente, documentos compartidos, códigos TI y licencias.
- Aceptación manual en navegador y job de retención de resultados pendientes.

**Sugerencia:** abrir como Draft hasta integrar 003/006 y repetir la validación integral. Base `develop`; no fusionar automáticamente.
