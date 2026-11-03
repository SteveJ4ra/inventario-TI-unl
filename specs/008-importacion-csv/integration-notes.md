# Notas de integración: importación CSV (008)

**Fecha:** 2026-11-02
**Commit base:** `origin/develop` = `161187c4d9f5d1855888545d2ffe797096b99ca6`
**Rama:** `feature/emilio-008-importacion-csv`

## Proveedores 003/006

En el commit base **no están integrados** los paquetes proveedores:

- `git ls-tree --name-only origin/develop backend/inventory/` no lista módulos de adquisiciones ni licencias.
- `git ls-tree -r --name-only origin/develop backend/inventory/migrations/` solo contiene `0001_initial.py` y `0002_integrity.py`.
- No existen `inventory/acquisition_services.py` ni `inventory/license_services.py`, ni los modelos `Faculty`, `AcquisitionDocument`, `AcquisitionLine`, `Asset` (de 003) o `SoftwareLicenseLot` (de 006).

Por eso 008 entrega orquestación, persistencia y UI completas, pero la frontera de producción queda explícita:

- `DjangoProviderGateway` busca los modelos y servicios en tiempo de ejecución.
- Si faltan, lanza `ProviderUnavailable`; las vistas responden **503** con `code: provider_unavailable`.
- Nunca se usa un fake en producción ni se devuelve un éxito ficticio.
- `FakeGateway` solo se activa en tests con `override_settings(IMPORT_GATEWAY=...)`.

## Contratos consumidos (a confirmar con 003/006)

| Uso | Contrato supuesto |
| --- | --- |
| Validar activos | modelos `Faculty`, `AcquisitionDocument`, `AcquisitionLine`, `Asset`; `Gateway.validate_assets(rows)` |
| Aplicar activos | `inventory.acquisition_services.import_assets(actor=..., rows=[values...])` |
| Validar licencias | modelo `SoftwareLicenseLot`; `Gateway.validate_license_lots(rows)` |
| Aplicar licencias | `inventory.license_services.import_license_lots(actor=..., rows=[values...])` |

Las filas entregadas al proveedor son los `values` normalizados, incluido `item_value` por fila y el documento compartido (`document_key`) o su id. El proveedor conserva la responsabilidad de reglas de adquisición/licencias, códigos automáticos y unicidad.

## Archivos compartidos y migraciones

Archivos modificados fuera de `inventory/imports/`:

- `backend/config/settings.py`: `IMPORT_*` y `IMPORT_GATEWAY`.
- `backend/.env.example`: límites documentados.
- `backend/inventory/models.py`: `ImportBatch` (sin FK a modelos proveedores para no bloquear el arranque).
- `backend/inventory/urls.py`: seis rutas nuevas bajo `/api/imports/`.
- `backend/inventory/migrations/0003_importbatch.py`: nueva tabla.
- `frontend/src/App.tsx`, `api.ts`, `types.ts`, `styles.css`: integración de la pantalla.

Grafo de migraciones local: `0001_initial` → `0002_integrity` → `0003_importbatch`. `makemigrations --check` devuelve `No changes detected` con PostgreSQL efímero. No se alteraron migraciones existentes.

## Regresiones ejecutadas

- Suite Django completa en PostgreSQL 17 efímero: 45 pruebas OK, incluidas las 17 de importación y concurrencia.
- Suite pura: 16 pruebas OK.
- Frontend: 20 pruebas OK y build de producción OK.
- CSRF multipart, permisos de gestor y sesión comprobados en la suite API.

## Acciones pendientes para auditoría

1. Integrar 003/006 en `develop` y verificar los nombres/firmas reales de los servicios. Ajustar `gateways.py` si difieren.
2. Confirmar que `import_assets` e `import_license_lots` participan de la transacción de `services.apply` y que un fallo de una fila revierte todas las escrituras de dominio.
3. Ejecutar casos reales de factura/respaldo compartido, códigos TI, fecha de inicio de licencia y unicidad concurrente.
4. Revisar si 003/006 exponen sus propios validadores; si es así, sustituir la validación delegada mínima para cumplir T004 sin duplicar reglas.
5. Actualizar `tasks.md` y esta nota al integrar proveedores; la feature no debe declararse integralmente validada antes de esa auditoría.
6. Definir el trabajo de retención de resultados (30 días) si se requiere purga automática; hoy el valor está configurado y el contenido temporal se elimina, pero no existe un job de purga.
