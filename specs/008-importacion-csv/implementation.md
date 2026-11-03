# Implementación: importación CSV (008)

**Fecha:** 2026-11-02
**Entorno:** Windows (win32, PowerShell 5.1); Python 3.13.14; Django 5.2.18; PostgreSQL 17; Node 24.18.0; npm 11.16.0.
**Rama:** `feature/emilio-008-importacion-csv`, creada desde `origin/develop` (`161187c4d9f5d1855888545d2ffe797096b99ca6`).
**Base de PR:** `develop` (nunca `main`; sin merge automático).

## Alcance entregado

- Plantillas CSV versionadas `assets-v1` y `license-lots-v1`, con BOM UTF-8, y ejemplos válidos.
- Parser CSV puro (sin Django) con cabeceras exactas, normalización, límites, errores completos por fila/campo, hash SHA-256 estable y validación de documentos compartidos.
- Persistencia de `ImportBatch` (preview inmutable), propiedad por gestor, expiración, cancelación, doble confirmación ligada al hash y aplicación idempotente con bloqueo de fila.
- API REST de plantillas, previews, consulta paginada, confirmación, aplicación y cancelación.
- UI de importación: tipo, descarga de plantilla, carga, errores, filas paginadas, resumen, dos confirmaciones explícitas, resultado y estados vencido/cancelado.
- Frontera de gateway hacia 003/006. En producción, si los proveedores no están integrados, responde 503 y nunca simula éxito. El fake es exclusivamente de pruebas.

## Tareas y requisitos

| Tarea | Estado | Evidencia |
| --- | --- | --- |
| T001 plantillas y ejemplos | [x] | `inventory/imports/templates/`, `examples/`; test de ejemplo versionado |
| T002 límites y TTL | [x] | `IMPORT_*` en settings y `.env.example`; tests de bytes/filas y expiración |
| T003 documentos compartidos/unicidad | [x] | Reglas XOR y metadatos en `domain.py`; conflicto de unicidad se delega al proveedor |
| T004 parser + validadores 003/006 | [ ] | Parser y validación CSV completos; reutilización real de validadores 003/006 pendiente de integración |
| T005 preview completa y hash | [x] | `services.preview`; preview no escribe dominio (test) |
| T006 doble confirmación | [x] | `services.confirm`; usuario/estado/hash; tests de hash y orden |
| T007 aplicar todo-o-nada/idempotencia | [ ] | Bloqueo, revalidación, rollback e idempotencia probados con fake; transacción real depende de 003/006 |
| T008 autorización, expiración, cancelación, límites | [x] | Servicios/vistas y tests de permisos, CSRF, TTL, cancelación y 413 |
| T009 frontend plantillas/carga/preview | [x] | `frontend/src/components/Import.tsx`; test de plantilla y carga |
| T010 errores y dos confirmaciones | [x] | Tabla de errores y segunda confirmación con tipo/número; test |
| T011 resultado y lote expirado/cancelado | [x] | Panel de resultado y estados; test de aplicación |
| T012 activos/licencias/errores/duplicados/documentos | [x] | Suite aislada y suite API con fake |
| T013 rollback/reintentos/concurrencia/límites | [x] | Tests de rollback de lote, reintento 200, concurrencia y límites |
| T014 evidencia | [x] | Este archivo, `validation.md`, `integration-notes.md` y `pr-description.md` |

FR cubiertos por la orquestación y UI: FR-001 a FR-012 en lo verificable sin proveedores; FR-007 y la parte de FR-004/FR-008 que dependen de la transacción real quedan sujetos a integración.

## Código y contratos

- `backend/inventory/imports/domain.py`: parser puro, esquemas, normalización, reglas de documentos, resumen y hash.
- `backend/inventory/imports/schemas.py`: tipos, versiones, columnas, rutas de plantillas/ejemplos y enums.
- `backend/inventory/imports/gateways.py`: `get_gateway`, `DjangoProviderGateway`, `ProviderUnavailable`.
- `backend/inventory/imports/services.py`: preview, consulta, expiración, confirmación, aplicación y cancelación.
- `backend/inventory/imports/views.py`: API, paginación, límites, CSRF y traducción de errores.
- `backend/inventory/models.py` + `migrations/0003_importbatch.py`: estado persistente del lote.
- `backend/inventory/urls.py`: rutas `/api/imports/...`.
- `backend/config/settings.py` y `.env.example`: `IMPORT_MAX_BYTES=2000000`, `IMPORT_MAX_ROWS=2000`, `IMPORT_PREVIEW_TTL_SECONDS=86400`, `IMPORT_RESULT_RETENTION_SECONDS=2592000`, `IMPORT_GATEWAY`.
- Frontend: `Import.tsx`, `api.ts` (multipart), `types.ts`, `App.tsx`, `styles.css`, `tests/import.test.tsx`.

## Decisiones técnicas

1. **Dominio puro y frontera explícita.** El parser y las reglas CSV no importan modelos ni 003/006. La semántica de facultades, documentos y licencias se delega al gateway; sin proveedor se devuelve 503, no datos ficticios.
2. **Hash estable.** Se calcula sobre filas normalizadas y resumen, no sobre bytes crudos. Quitar BOM/espacios externos no cambia el hash; cambiar contenido sí. Ambas confirmaciones exigen el mismo hash.
3. **Preview inmutable.** Las filas se guardan normalizadas y no se leen del archivo en confirmar/aplicar. Se borran al aplicar, cancelar o vencer; la retención del resultado no conserva CSV temporal.
4. **Aplicación segura.** `select_for_update` sobre `ImportBatch`, revalidación contra el gateway y transacción anidada. Cualquier error deja el lote sin estado APPLIED y sin escrituras de la importación. Un segundo apply devuelve 200 con el resultado ya guardado.
5. **Documentos.** `acquisition_document_id` XOR `document_key`; un mismo `document_key` exige metadatos idénticos y no fusiona por referencia textual. `item_value` se conserva por fila.
6. **Límites y errores.** 2 MB y 2000 filas; 413 para excesos. El preview inválido devuelve 400 con `batch_id`, `errors` y todas las filas, sin habilitar confirmación.

## Ejecución

- `python -m unittest discover -s backend/inventory/isolated_tests/imports -p "test_*.py"`: 16 pruebas OK.
- `python backend/tools/test_postgres.py`: 45 pruebas OK en PostgreSQL 17 efímero (incluye 17 de importación y concurrencia).
- `npm test -- --run`: 20 pruebas OK (8 archivos).
- `npm run build`: `tsc --noEmit` y Vite OK.
- `manage.py makemigrations --check --dry-run` (PostgreSQL efímero): `No changes detected`, salida 0.

## Pendientes y revisión humana

- Integrar 003/006 y confirmar los nombres/firmas reales de sus servicios de importación. `DjangoProviderGateway` usa contratos supuestos (`inventory.acquisition_services.import_assets`, `inventory.license_services.import_license_lots`) y modelos `Faculty`, `AcquisitionDocument`, `AcquisitionLine`, `Asset`, `SoftwareLicenseLot`.
- Ejecutar pruebas con proveedores reales: atomicidad de datos de dominio, unicidad concurrente, documentos compartidos y códigos TI.
- Aceptación manual en navegador con ambas plantillas y revisión humana del PR. No se declara la feature integralmente validada.
- Participación de IA: implementación, pruebas y documentación asistidas por el agente; revisión humana real pendiente.
