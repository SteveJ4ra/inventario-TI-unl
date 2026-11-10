# Validación: importación CSV

**Fecha:** 2026-11-01  
**Entorno:** Windows, Python 3.13.14, Django 5.2.18, Node 24.18.0, npm 11.16.0, PostgreSQL 17 temporal.  
**Base:** `161187c4d9f5d1855888545d2ffe797096b99ca6`.

## Resumen

| Suite | Comando | Resultado |
|---|---|---|
| Parser puro | `& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend\inventory\isolated_tests\imports -v` | **PASS** — 13 pruebas |
| Backend/API/DB | `& .\backend\.venv\Scripts\python.exe backend\tools\test_postgres.py inventory --verbosity 1` | **PASS** — 43 pruebas |
| Frontend | `npm.cmd --prefix frontend test -- --run` | **PASS** — 20 pruebas, 8 archivos |
| Build frontend | `npm.cmd --prefix frontend run build` | **PASS** |
| Dependencias | `& .\backend\.venv\Scripts\python.exe -m pip check` | **PASS** — sin dependencias rotas |
| Django check | `& .\backend\.venv\Scripts\python.exe backend\manage.py check` | **PASS** — 0 issues |
| Migraciones pendientes | `& .\backend\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run` | **PASS** — no changes detected |
| Espacios/conflictos | `git diff --check` | **PASS** — sin errores de espacio |

Nota: `manage.py test` directo contra la base local falló con `permission denied to create database`; por eso los tests Django se ejecutaron con el runner PostgreSQL temporal incluido, que no toca la base local ni concede `CREATEDB` al rol de aplicación.

## Cobertura por caso

| Caso | Evidencia | Estado |
|---|---|---|
| Cabeceras, versión, UTF-8/BOM y archivo sin filas | `test_import_parsing.py`; `test_imports.py::test_bad_header_and_empty_file_are_invalid` | PASS |
| Normalización de activos, condicionales compra/donación y fecha desconocida | `test_import_parsing.py` | PASS |
| Documentos compartidos y discrepancia de metadatos | `test_asset_rejects_inconsistent_document_metadata` | PASS |
| Duplicado de identidad dentro del archivo | `test_asset_rejects_duplicate_identity` | PASS |
| Licencias: cantidades, fechas y resumen de válidos | `test_license_lot_validates_quantities_and_dates` | PASS |
| Límites de bytes y filas | `test_limits_are_enforced`; `test_imports.py::test_upload_limits_return_413` | PASS |
| Preview válido sin escrituras de dominio | `test_valid_asset_preview_returns_complete_batch_without_writing` | PASS |
| Preview inválido con 400, `batch_id` y errores completos | `test_invalid_preview_returns_400_with_all_errors_and_batch_id` | PASS |
| Hash incorrecto y estados conflictivos | `test_hash_and_state_conflicts`; `test_invalid_preview_cannot_be_confirmed` | PASS |
| Doble confirmación y aplicación | `test_confirm_apply_and_idempotent_retry`; frontend `imports.test.tsx` | PASS |
| Reintento APPLIED devuelve 200 sin duplicar | `test_confirm_apply_and_idempotent_retry` | PASS |
| Rollback integral ante fallo del adaptador | `test_adapter_failure_rolls_back_all_writes_and_keeps_preview` | PASS |
| Expiración elimina contenido y bloquea confirmación | `test_expired_preview_is_hidden_and_cannot_confirm` | PASS |
| Cancelación elimina filas | `test_cancel_clears_rows_and_cannot_cancel_applied` | PASS |
| Propietario, Gestor, anónimo y CSRF | `test_owner_and_manager_permissions`; `test_session_writes_require_csrf` | PASS |
| Paginación de filas | `test_get_rows_are_paginated` | PASS |
| Plantillas y tipo de lote de licencias | `test_license_lot_preview_and_template`; frontend `imports.test.tsx` | PASS |
| Regresión de 002 | Suite completa de 43 pruebas | PASS |

## Estados no ejecutados o bloqueados

| Caso | Estado | Motivo |
|---|---|---|
| Aplicación real de activos/lotes con 003/006 | **DEPENDENCIA NO INTEGRADA** | Los paquetes proveedores no existen en código; los adaptadores responden 409 `dependency_not_integrated`. |
| SC-005: códigos TI y activos Disponibles/sin custodio generados por importación | **NO EJECUTADO** | Requiere adaptador real de 003. |
| Concurrencia real de dos `apply` simultáneos | **NO EJECUTADO** | Hay bloqueo e idempotencia, pero no prueba de carrera con dos conexiones. |
| Recorrido manual web con backend real | **NO EJECUTADO** | No se aplicó `0003` a la base local ni se levantó el servidor por falta de autorización. |
| Migración aplicada | **NO EJECUTADO** | Solo se generó y verificó el archivo; `showmigrations` local sigue mostrando `[ ]` para 0001–0003. |

## Conclusión

La lógica propia, la API, la persistencia temporal y la interfaz están verificadas con PostgreSQL real temporal y pruebas de frontend. La feature **no** se declara integralmente validada: faltan los adaptadores 003/006, la prueba de carrera y el recorrido manual sobre una base migrada.
