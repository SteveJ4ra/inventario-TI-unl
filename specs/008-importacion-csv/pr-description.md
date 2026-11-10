# feat: 008-importacion-csv

**Base:** `develop`  
**Head:** `feature/emilio-008-importacion-csv`  
**Estado:** Draft — integración real con 003/006 pendiente.

## Resumen

Implementa importación CSV estricta para activos y lotes de licencias: plantillas versionadas, validación completa, preview inmutable, errores por fila/campo, doble confirmación del Gestor propietario, aplicación atómica e idempotente, expiración/cancelación y pantalla web.

## SDD

- [Especificación](spec.md)
- [Plan](plan.md)
- [Tareas](tasks.md)
- [Implementación](implementation.md)
- [Validación](validation.md)
- [Notas de integración](integration-notes.md)
- [Contratos API](contracts/api.md)
- [Contrato web](contracts/web.md)

## Cambios principales

### Backend

- Plantillas `assets-v1.csv` y `license-lots-v1.csv`.
- Parser puro con normalización, reglas condicionales de compra/donación, documentos compartidos, duplicados y hash SHA-256.
- Modelos `ImportBatch` e `ImportBatchRow`; migración `inventory.0003_importbatch_importbatchrow_and_more` (no aplicada).
- Endpoints:
  - `GET /api/imports/templates/{kind}/`
  - `POST /api/imports/previews` (201 válido / 400 inválido / 413 límites)
  - `GET /api/imports/{batch_id}` (filas paginadas)
  - `POST /api/imports/{batch_id}/confirm`
  - `POST /api/imports/{batch_id}/apply` (201 primera vez / 200 reintento)
  - `POST /api/imports/{batch_id}/cancel`
- Autorización de Gestor y propietario, CSRF, expiración, bloqueo transaccional y errores de estado.
- Adaptadores de producción explícitos para 003/006; sin fakes de producción.

### Frontend

- Navegación «Importaciones».
- Descarga de plantilla, carga por tipo y versión.
- Vista previa paginada, resumen de filas válidas y advertencia de creación masiva.
- Errores por fila/campo y descarga CSV de errores.
- Primera confirmación y confirmación final con conteo/tipo.
- Resultado final, lote expirado/cancelado y referencia del lote.

## Pruebas ejecutadas

| Comando | Resultado |
|---|---|
| `python -m unittest discover -s backend\inventory\isolated_tests\imports -v` | PASS — 13 |
| `python backend\tools\test_postgres.py inventory --verbosity 1` | PASS — 43 |
| `npm.cmd --prefix frontend test -- --run` | PASS — 20 |
| `npm.cmd --prefix frontend run build` | PASS |
| `pip check` | PASS |
| `manage.py check` | PASS |
| `makemigrations --check --dry-run` | PASS |
| `git diff --check` | PASS |

La suite de backend usa PostgreSQL 17 temporal; no toca la base local ni concede `CREATEDB` al rol de aplicación.

## Dependencias y límites

- **003-fichas-adquisiciones** y **006-lotes-licencias** no están implementados en código. Los adaptadores por defecto devuelven 409 `dependency_not_integrated`.
- No se probó creación real de activos/lotes, códigos TI, unicidad concurrente ni revalidación de dominio contra DB.
- No se aplicó la migración `0003` ni se ejecutó recorrido manual con servidor real.
- El contrato de `confirm`/`apply` no define el cuerpo; se implementó `content_hash` y se deja para revisión humana.
- Límites: 5 MiB, 1.000 filas, preview de 30 minutos; configurables por entorno.

## Pendiente antes de retirar Draft

1. Integrar 003/006 e implementar adaptadores reales.
2. Probar aplicación atómica real y concurrencia.
3. Aplicar migración tras revisión y ejecutar `quickstart.md`.
4. Actualizar evidencia y repetir regresiones.

No fusionar automáticamente. Revisión por otro integrante según `CONTRIBUTING.md`.
