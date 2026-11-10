# feat: fichas, facultades y adquisiciones 003

Base: develop. Head: Alex_Sigcho_Feature. Estado recomendado: Draft. Este archivo prepara el cuerpo del PR; no existe publicación de PR ni commits nuevos realizados por el agente.

## Problema y comportamiento entregado

El inventario necesitaba documentar compras/donaciones compartidas y corregir fichas preservando su historia. Se incorporan documentos y líneas por activo, facultades, Operador y servicios auditados. Un respaldo puede compartirse entre varios activos conservando valores individuales y moneda histórica, sin imágenes ni adjuntos.

- Registro manual en dos solicitudes: documento primero, después cada activo + línea atómicos.
- Asociación inicial de activos existentes sin adquisición, con revisión/motivo/fecha y transacción global.
- Edición de activos/custodios y documento compartido con snapshots, autorización backend, CSRF y rollback. El documento exige snapshot y revisiones de todos los afectados, incluso protege metadatos cuando está vacío.
- Catálogo de facultades y permisos Gestor/Operador separados; React muestra diferencias confirmables e historial combinado.
- Proveedor real import_assets para 008: compras por document_key y documento existente, con idempotencia de lote y sin éxitos simulados.

## Migraciones y despliegue

0004_acquisition_expansion depende de 0003_importbatch y mantiene Asset.faculty nullable temporalmente; instala tablas, constraints y conservación SQL. No realiza backfill. Solo se ha aplicado en PostgreSQL temporal.

El comando acquisition_preflight es de solo lectura. La plantilla faculty_contract.py.txt está fuera del grafo activo y no debe promoverse sin mapeo verificado y revisión de escritores legados. No se aplicó migrate ni se modificó .env/base local.

## Validación ejecutada

- Backend completo: 182/182 PASS en PostgreSQL temporal, incluidas migración, integridad, concurrencia y gateway 008 real.
- Frontend: 57/57 PASS; TypeScript/Vite PASS.
- check: sin incidencias; makemigrations --check --dry-run: No changes detected, ambos mediante runner aislado.
- pip check y git diff --check correctos.
- Sin recorrido manual de navegador ni despliegue local.

## Límites para revisión

- T004: falta contracción activa, mapeo verificado donde exista legado y revisión de escritores.
- T005/T011: cero/negativos y fecha documental de donación pendientes; rechazo explícito.
- Donación CSV nueva bloqueada por decisión humana; no se infiere tipo de respaldo de una descripción.
- 005 no integrado: cambio posterior de facultad da 503; sus pruebas permitidas usan sustitutos solo en tests.
- T007/T015/T016/T017 siguen parciales por esa dependencia.
- Cambio de origen no habilitado. Licencias 006 fuera de alcance.

11 tareas completas y 7 parciales; detalle en [tasks.md](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/tasks.md). No afirmar aceptación integral de 003 ni aprobación de políticas institucionales. Revisión humana necesaria antes de publicar/integrar.

## Evidencia

[Implementación](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/implementation.md) · [Validación](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/validation.md) · [Integración](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/integration-notes.md) · [Inventario de archivos](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/file-inventory.md) · [Quickstart](https://github.com/SteveJ4ra/inventario-TI-unl/blob/Alex_Sigcho_Feature/specs/003-fichas-adquisiciones/quickstart.md)

Referencia local de integración consultada: origin/develop 4247cc8998ed810fdb6462941d85f3324260a2ec, sin fetch reciente. No auto-merge ni destino main.

Los enlaces de evidencia apuntan a la rama de trabajo y serán revisables en remoto después de publicarla; no constituyen un PR ya creado.
