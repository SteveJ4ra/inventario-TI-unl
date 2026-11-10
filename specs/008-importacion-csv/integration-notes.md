# Integración: importación CSV

**Fecha:** 2026-11-01  
**Commit base:** `161187c4d9f5d1855888545d2ffe797096b99ca6` (`origin/develop`)  
**Rama:** `feature/emilio-008-importacion-csv`

## Proveedores

| Paquete | Estado en código | Uso desde 008 |
|---|---|---|
| 003-fichas-adquisiciones | Ausente | El adaptador real debe crear/validar `AcquisitionDocument`, `AcquisitionLine`, facultad, activo, código TI y estado inicial. |
| 006-lotes-licencias | Ausente | El adaptador real debe crear/validar `SoftwareLicenseLot` con cantidades, fechas y reglas de 006. |

Los contratos de ambos paquetes se leyeron desde `specs/003-fichas-adquisiciones/` y `specs/006-lotes-licencias/`. No se crearon modelos paralelos ni se copiaron sus tablas.

## Contrato de adaptadores

`settings.IMPORT_ADAPTERS` apunta a:

- `inventory.imports.adapters.UnavailableAssetAdapter`
- `inventory.imports.adapters.UnavailableLicenseLotAdapter`

Ambos fallan de forma explícita con `ImportDependencyUnavailable`, que la API transforma en **409 `dependency_not_integrated`**. No devuelven éxito ficticio ni escriben datos de dominio.

El adaptador real debe exponer:

```python
apply(rows, *, actor) -> dict
```

Responsabilidades del adaptador:

- Revalidar contra la base actual referencias de facultad/documento y unicidad de identidad.
- Crear documentos compartidos por `acquisition_document_id` o `document_key` coherente.
- Generar códigos TI y dejar activos en Disponible/sin custodio.
- Crear cada fila de licencias como un lote, no como asientos individuales.
- Escribir dentro de la transacción abierta por `service.apply`; cualquier excepción debe propagarse.
- Devolver un resultado serializable (conteos/referencias) para conservarlo en `applied_result`.

La orquestación ya revalida propietario, estado, hash, existencia de filas y consistencia de conteos. La revalidación de dominio contra DB no puede probarse hasta integrar los proveedores.

## Migraciones

Grafo actual:

```text
inventory.0001_initial
  -> inventory.0002_integrity
    -> inventory.0003_importbatch_importbatchrow_and_more
```

`0003` crea `ImportBatch`, `ImportBatchRow`, el índice `(actor, state)` y la restricción única `(batch, row_number)`. No se aplicó a la base local. `showmigrations inventory` muestra `[ ]` para 0001, 0002 y 0003; no se ejecutó `migrate` real.

## Archivos compartidos modificados

- `backend/config/settings.py`: límites y rutas de adaptadores.
- `backend/inventory/models.py`: se añadieron modelos al final; no se modificaron los modelos de 002.
- `backend/inventory/urls.py`: rutas nuevas sin cambiar las existentes.
- `backend/.env.example`: variables de importación documentadas.
- `frontend/src/App.tsx`: navegación Inventario/Importaciones; no se alteró el flujo de 002.
- `frontend/src/api.ts`: soporte de `FormData` y payload de error; compatible con llamadas JSON existentes.
- `frontend/src/types.ts`, `styles.css`: adiciones; sin eliminar estilos previos.

## Regresiones ejecutadas

- Suite completa `inventory`: **43 pruebas PASS**, incluye los tests de 002.
- Frontend completo: **20 pruebas PASS**, incluye navegación y flujos existentes.
- `tsc --noEmit` y build de Vite: **PASS**.
- `makemigrations --check --dry-run`: sin cambios adicionales.

## Acciones pendientes para auditoría

1. Integrar 003 y 006 en `develop`; implementar adaptadores reales y eliminar los `Unavailable...` del flujo de producción.
2. Probar aplicación atómica real, revalidación contra DB, documentos compartidos, códigos TI y rollback con modelos proveedores.
3. Añadir prueba de carrera de dos `apply` simultáneos sobre PostgreSQL.
4. Revisar y aplicar `0003`; ejecutar el recorrido manual de `quickstart.md` con base migrada.
5. Actualizar `validation.md`/`implementation.md` y retirar el estado Draft del PR cuando la integración esté verificada.

## Riesgos conocidos

- Sin proveedores, el usuario puede completar preview y ambas confirmaciones, pero la aplicación final devuelve 409 explicativo.
- La retención de filas es temporal; expiración/cancelación/aplicación las eliminan. El hash y el resultado mínimo permanecen.
- La API asume `content_hash` en `confirm` y `apply` porque el contrato no detalla el cuerpo. Debe ratificarse en revisión humana.
- La UI muestra filas paginadas de 50; si cambia `PAGE_SIZE` debe ajustarse el umbral visual.
