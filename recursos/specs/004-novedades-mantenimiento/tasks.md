# Tareas: novedades, pérdida y mantenimiento

**Estado:** T001–T017 completadas para el alcance independiente de 004. Revisión humana e integración con 005 pendientes.

## Fundamentos

- [x] T001 Probar transiciones de localización, condición, asignación, pérdida/robo y mantenimiento activo en backend/inventory/tests/test_incidents.py y backend/inventory/tests/test_maintenance.py.
- [x] T002 Añadir LifecycleStatus, assignment nullable para No localizado/Baja, reemplazo de asset_custody_consistent y snapshots con migración compatible en backend/inventory/models.py y backend/inventory/migrations/.
- [x] T003 Implementar Incident, MaintenanceEvent y RecoveryEvent con constraints en backend/inventory/models.py.
- [x] T004 Añadir servicios transaccionales, revisión global y guardas para que rectificaciones de 002 no ignoren eventos nuevos; validar revision/estado en backend/inventory/services.py.
- [x] T005 Exponer rutas, permisos y errores de conflicto en backend/inventory/views.py y backend/inventory/urls.py.

## US1 — Novedad de daño/observación

- [x] T006 [US1] Implementar alta, consulta y resolución con nota en backend/inventory/serializers.py y backend/inventory/services.py.
- [x] T007 [US1] Mostrar alertas pendientes y formulario de resolución en frontend/src/components/IncidentPanel.tsx.
- [x] T008 [US1] Probar activo asignado, nota requerida, condición sin cambio y resolución auditada en backend/inventory/tests/test_incidents.py y frontend/src/tests/incidents.test.tsx.

## US2 — Mantenimiento

- [x] T009 [US2] Implementar inicio/cierre, ubicación previa, taller, resultado e interrupción en backend/inventory/services.py.
- [x] T010 [US2] Bloquear entrega en servicio y API si hay mantenimiento En curso en backend/inventory/services.py.
- [x] T011 [US2] Añadir UI de taller, lista de ubicaciones históricas, confirmación y cierre en frontend/src/components/MaintenancePanel.tsx.
- [x] T012 [US2] Probar mantenimiento preventivo Operativo, bloqueo de entrega, cierre y confirmación de ubicación en backend/inventory/tests/test_maintenance.py y frontend/src/tests/maintenance.test.tsx.

## US3 — No localizado y recuperación

- [x] T013 [US3] Implementar snapshots y transición por pérdida/robo, incluida interrupción de mantenimiento en backend/inventory/services.py.
- [x] T014 [US3] Implementar recuperación con condición/ubicación y mismo código en backend/inventory/services.py.
- [x] T015 [US3] Mostrar último estado, custodio y ubicación sin presentar asignación vigente en la ficha existente (frontend/src/App.tsx y frontend/src/components/Inventory.tsx).
- [x] T016 [US3] Probar pérdida desde Disponible, Asignado y mantenimiento; recuperación e historial en backend/inventory/tests/test_incidents.py y frontend/src/tests/recovery.test.tsx.
- [x] T017 Actualizar historial, API docs y quickstart en specs/004-novedades-mantenimiento/ y README.md.

## Dependencias

US1 y US2 dependen de fundamentos. US3 depende de LifecycleStatus y puede integrarse con el modelo de mantenimiento. Baja aprobada pertenece a 005.

## Evidencia del bloque 1

- 54 pruebas de backend aprobadas con `backend/tools/test_postgres.py` en PostgreSQL temporal con ICU, incluidas nueve pruebas nuevas de modelos y migración.
- La prueba de migración aplica `0004_asset_lifecycle_events` sobre activos e historial creados bajo `0003_importbatch` y verifica su conservación.
- T001 cubre estados y transiciones a nivel de persistencia. Los recorridos por servicios, API y web se validarán en sus tareas correspondientes.
- `0004_asset_lifecycle_events` se aplicó en `inventario_ti` tras confirmar que no había activos previos. `showmigrations` muestra `0001`–`0004` aplicadas y `manage.py check` pasó. Las restricciones nuevas se verificaron en PostgreSQL y el trigger de inmutabilidad de movimientos sigue activo.

## Evidencia del bloque 2

- 61 pruebas aprobadas con `backend/tools/test_postgres.py inventory --verbosity 1` en PostgreSQL temporal con ICU. Los casos nuevos cubren bloqueo entre 002 y 004, rectificación, rollback, evidencia inmutable y permisos.
- El historial unificado ordena por revisión y deja vigente el contrato histórico de `/movements/`. El detalle de mantenimiento entrega la ubicación previa y la revisión del activo.
- T004 aporta la operación compartida para registrar evidencia. Las reglas y endpoints de escritura específicos se incorporarán en T006–T017. Los permisos de Operador y Revisor pertenecen a sus paquetes.
- `inventory.0005_asset_transition_evidence` se aplicó con resultado `OK` en `inventario_ti` como `inventario_app` en el puerto local 5432. El plan contenía únicamente `0005`. El SQL de avance crea la tabla de evidencia y sus protecciones. Las siete tablas de inventario existentes conservaron sus recuentos de filas (cero antes y después).
- `showmigrations inventory` confirmó `0001`–`0005` aplicadas y el plan global quedó sin pendientes. `manage.py check` pasó. PostgreSQL confirmó seis restricciones validadas, cuatro índices válidos y el trigger activo que protege la evidencia de modificaciones y borrados. La tabla nueva quedó vacía.

## Evidencia del bloque 3

- `GET/POST /api/assets/{id}/incidents/` consulta o registra daños y observaciones. `POST /api/incidents/{id}/resolve/` exige nota. Ambas escrituras usan la revisión global y guardan evidencia inmutable en la misma transacción.
- 67 pruebas aprobadas con `backend/tools/test_postgres.py inventory --verbosity 1` en PostgreSQL temporal con ICU. Los seis casos nuevos cubren activo asignado, permisos y CSRF, datos inválidos, conflictos, concurrencia y rollback.
- 23 pruebas aprobadas con `npm.cmd --prefix frontend test -- --run`. Los tres casos nuevos usan una API simulada para verificar registro y resolución en la ficha, historial, errores y recarga ante conflicto. `npm.cmd --prefix frontend run build` pasó.
- `manage.py check` y `makemigrations --check --dry-run` pasaron. `migrate --plan` no mostró operaciones pendientes. El bloque no requiere migración.

## Evidencia del bloque 4

- La API inicia y cierra mantenimiento con revisión esperada y evidencia inmutable. La ficha identifica el mantenimiento activo y consulta el detalle para precargar la ubicación anterior. El filtro Disponible excluye activos en mantenimiento, aunque su asignación interna se conserve. El cambio de condición sigue siendo una operación separada.
- La interrupción por No localizado está disponible como servicio interno sin resultado de reparación. Su integración con el reporte de pérdida o robo queda en T013.
- 74 pruebas aprobadas con `backend/tools/test_postgres.py inventory --verbosity 1` en PostgreSQL temporal con ICU. Los siete casos nuevos cubren inicio, cierre, elegibilidad, ubicación, condición, permisos y CSRF, conflicto entre entrega e inicio, rollback e inmutabilidad.
- 25 pruebas aprobadas con `npm.cmd --prefix frontend test -- --run`. Los dos casos nuevos usan API simulada y cubren la ficha, el inicio, la confirmación de una ubicación editable, el historial y errores. `npm.cmd --prefix frontend run build` pasó.
- `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` pasaron. `migrate --plan` no mostró operaciones pendientes.

## Evidencia del bloque 5

- `POST /api/assets/{id}/incidents/` registra pérdida o robo y separa la custodia vigente de su snapshot. El reporte y la interrupción, cuando corresponde, se registran con revisiones consecutivas en la misma transacción.
- `POST /api/assets/{id}/recover/` requiere `inspection_confirmed: true`, `inspected_condition` y `recovered_location`. Conserva código, vincula el reporte y registra la recuperación sin reactivar el mantenimiento.
- La ficha existente muestra el último estado, condición, ubicación y custodio en No localizado. El historial unificado conserva el reporte, la interrupción y la recuperación.
- 82 pruebas aprobadas con `backend/tools/test_postgres.py inventory --verbosity 1` en PostgreSQL temporal con ICU. Los ocho casos nuevos cubren escenarios de pérdida, recuperación, permisos, CSRF, concurrencia y rollback.
- 26 pruebas aprobadas con `npm.cmd --prefix frontend test -- --run` y compilación correcta. La prueba de recuperación usa API simulada. `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` pasaron. `0001`–`0005` están aplicadas y el plan quedó sin pendientes.
- En `recover_asset` quedó documentado el punto donde 005 podrá cancelar solicitudes pendientes dentro del mismo bloqueo y transacción. Esa integración requiere el proveedor de 005 y permanece pendiente.

## Evidencia del bloque 6

- El contrato de API documenta el orden de revisión del historial, el detalle de mantenimiento y los campos de escritura comprobados. El quickstart incluye el segundo inicio de mantenimiento antes del robo.
- El 4 de noviembre de 2026 pasaron 83 pruebas backend en PostgreSQL temporal con ICU, 26 pruebas frontend y el build. El recorrido en Chrome real con Django, Vite y PostgreSQL temporal pasó con diez revisiones y dos movimientos legados.
- [Implementación](implementation.md), [validación](validation.md), [integración](integration-notes.md) y [borrador del PR](pr-description.md). La base de desarrollo conserva las migraciones `0001`–`0005` aplicadas y cero pendientes.

## Trazabilidad FR → tareas

- FR-001–FR-004: T001, T006–T008
- FR-005–FR-009: T001–T005, T009–T012
- FR-010–FR-014: T001–T005, T013–T016
- FR-015–FR-016: T001–T004, T008, T012, T016
