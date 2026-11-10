# Implementación: importación CSV

**Fecha:** 2026-11-01  
**Rama:** `feature/emilio-008-importacion-csv`  
**Base:** `161187c4d9f5d1855888545d2ffe797096b99ca6` (`origin/develop`)  
**Entorno:** Windows, Python 3.13.14, Django 5.2.18, Node 24.18.0, npm 11.16.0, PostgreSQL 17 temporal para pruebas.

## Alcance entregado

- Plantillas separadas y versionadas `assets-v1.csv` y `license-lots-v1.csv`, con las cabeceras exactas y descarga autenticada.
- Parser CSV puro con normalización, validación completa, hash canónico SHA-256, límites y errores por fila/campo.
- Modelos `ImportBatch` e `ImportBatchRow`, con filas normalizadas inmutables, propietario, estado, hash, expiración y resultado de aplicación.
- API de preview, consulta paginada, confirmación, aplicación idempotente y cancelación bajo `/api/imports/`.
- Doble confirmación ligada al hash y al mismo Gestor propietario; bloqueo transaccional del lote y rollback ante fallo del adaptador.
- Pantalla web de importación con descarga de plantilla, carga, vista previa paginada, errores descargables, resumen, advertencia de creación masiva, primera confirmación y confirmación final.
- Migración `inventory.0003_importbatch_importbatchrow_and_more`, generada pero **no aplicada** a la base local.

## Tareas y requisitos

| Tarea | Estado | Detalle |
|---|---|---|
| T001 | Completa | Plantillas `assets-v1.csv` y `license-lots-v1.csv`; pruebas verifican cabeceras. |
| T002 | Completa | `IMPORT_MAX_BYTES=5242880`, `IMPORT_MAX_ROWS=1000`, `IMPORT_PREVIEW_TTL_MINUTES=30` configurables. |
| T003 | Parcial | Documentos compartidos y discrepancias resueltos en parser. Unicidad concurrente real queda delegada a los adaptadores 003/006. |
| T004 | Parcial | Parser CSV seguro implementado. No se reutilizaron validadores de 003/006 porque esos paquetes aún no existen en código. |
| T005 | Completa | Vista previa completa, errores saneados, hash estable y filas normalizadas persistidas. |
| T006 | Completa | Confirmación previa y final con hash, estado, propietario y bloqueo. |
| T007 | Parcial | Orquestación atómica, idempotencia 201/200 y rollback probados con fake. Aplicación real y revalidación de dominio dependen de adaptadores 003/006. |
| T008 | Completa | Autorización de Gestor/propietario, expiración, cancelación, CSRF y límites 413. |
| T009 | Completa | Plantilla, carga y vista previa completa paginada en React. |
| T010 | Completa | Errores por fila/campo, descarga de errores y dos confirmaciones explícitas. |
| T011 | Completa | Resultado final, referencia del lote y estados expirado/cancelado. |
| T012 | Completa | Pruebas de activos, licencias, errores múltiples, duplicados y documentos compartidos. |
| T013 | Parcial | Rollback, reintento y límites probados. Carrera real de aplicación simultánea pendiente. |
| T014 | Completa | Evidencia registrada en `validation.md`. |

**FR cubiertos:** FR-001 a FR-012 en la medida permitida por la ausencia de 003/006.  
**SC cubiertos con pruebas:** SC-001, SC-002, SC-003 (con fake), SC-004, SC-006. SC-005 queda pendiente de los adaptadores reales.

## API entregada

| Método y ruta | Resultado |
|---|---|
| `GET /api/imports/templates/{kind}/` | Plantilla CSV de activos o licencias. |
| `POST /api/imports/previews` | 201 con lote válido; 400 con lote inválido y errores completos; 413 por límites. |
| `GET /api/imports/{batch_id}` | Estado, resumen, errores y filas paginadas; solo propietario Gestor. |
| `POST /api/imports/{batch_id}/confirm` | Primera confirmación; exige `content_hash`. |
| `POST /api/imports/{batch_id}/apply` | Confirma y aplica; 201 la primera vez, 200 al reintentar APPLIED. |
| `POST /api/imports/{batch_id}/cancel` | Descarta el lote y elimina sus filas temporales. |

## Decisiones técnicas

- **Cabeceras exactas y ordenadas:** el archivo debe conservar la plantilla; se admite BOM UTF-8 y se rechaza cualquier otra codificación.
- **Resumen de válidos:** los totales de dominio del resumen cuentan únicamente filas válidas; las filas con error siguen visibles para corrección.
- **Hash inmutable:** SHA-256 sobre `kind`, `schema_version` y filas normalizadas en orden canónico. Confirmar o aplicar con otro hash devuelve 409.
- **Persistencia temporal:** las filas se guardan normalizadas. Al expirar, cancelar o aplicar se eliminan; el hash, resumen y resultado mínimo se conservan para trazabilidad e idempotencia.
- **Propiedad exclusiva:** además de `IsManager`, el servicio comprueba que el actor sea el creador del lote.
- **Bloqueo:** `select_for_update()` sobre el lote evita confirmaciones/aplicaciones concurrentes del mismo lote.
- **Idempotencia:** un `apply` repetido sobre APPLIED valida el hash y devuelve el resultado anterior con 200.
- **Adaptadores:** se configuran en `settings.IMPORT_ADAPTERS`. Los adaptadores por defecto fallan con `dependency_not_integrated`; no simulan éxito ni escriben datos ficticios.
- **Revalidación:** la orquestación revalida estado, hash, filas y propiedad. La revalidación de referencias, facultad, documento compartido y unicidad contra la base actual corresponde al adaptador de 003/006 al aplicar.
- **Sin migración aplicada:** `makemigrations` creó el archivo; no se ejecutó `migrate` real por falta de autorización.

## Archivos principales

- `backend/inventory/imports/schemas.py`
- `backend/inventory/imports/parsing.py`
- `backend/inventory/imports/storage.py`
- `backend/inventory/imports/service.py`
- `backend/inventory/imports/adapters.py`
- `backend/inventory/imports/exceptions.py`
- `backend/inventory/imports/serializers.py`
- `backend/inventory/imports/views.py`
- `backend/inventory/imports/templates/`
- `backend/inventory/models.py`
- `backend/inventory/migrations/0003_importbatch_importbatchrow_and_more.py`
- `frontend/src/components/Imports.tsx`
- `frontend/src/App.tsx`, `api.ts`, `types.ts`, `styles.css`
- `backend/inventory/tests/test_imports.py`
- `backend/inventory/isolated_tests/imports/test_import_parsing.py`
- `frontend/src/tests/imports.test.tsx`

## Participación de IA y revisión humana

Implementación asistida por agente de código a partir de la guía de Emilio y los documentos SDD. La revisión funcional humana, la aceptación del contrato de `content_hash` y la integración con los proveedores 003/006 están **pendientes**. No se declara la feature integrada ni aprobada.

## Pendientes

- Implementar adaptadores reales cuando 003 y 006 estén en `develop`; sustituir los adaptadores `Unavailable...`.
- Definir y probar concurrencia real de dos aplicaciones simultáneas y conflictos de unicidad contra DB.
- Aplicar `0003` tras revisión y ejecutar el recorrido manual de `quickstart.md`.
- Actualizar la evidencia tras integrar proveedores y repetir regresiones.
