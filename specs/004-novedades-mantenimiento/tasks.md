# Tareas: novedades, pérdida y mantenimiento

**Estado:** planeadas; no ejecutadas.

## Fundamentos

- [ ] T001 Probar transiciones de localización, condición, asignación, pérdida/robo y mantenimiento activo en backend/inventory/tests/test_incidents.py y backend/inventory/tests/test_maintenance.py.
- [ ] T002 Añadir LifecycleStatus, assignment nullable para No localizado/Baja, reemplazo de asset_custody_consistent y snapshots con migración compatible en backend/inventory/models.py y backend/inventory/migrations/.
- [ ] T003 Implementar Incident, MaintenanceEvent y RecoveryEvent con constraints en backend/inventory/models.py.
- [ ] T004 Añadir servicios transaccionales, revisión global y guardas para que rectificaciones de 002 no ignoren eventos nuevos; validar revision/estado en backend/inventory/services.py.
- [ ] T005 Exponer rutas, permisos y errores de conflicto en backend/inventory/views.py y backend/inventory/urls.py.

## US1 — Novedad de daño/observación

- [ ] T006 [US1] Implementar alta, consulta y resolución con nota en backend/inventory/serializers.py y backend/inventory/services.py.
- [ ] T007 [US1] Mostrar alertas pendientes y formulario de resolución en frontend/src/components/IncidentPanel.tsx.
- [ ] T008 [US1] Probar activo asignado, nota requerida, condición sin cambio y resolución auditada en backend/inventory/tests/test_incidents.py y frontend/src/tests/incidents.test.tsx.

## US2 — Mantenimiento

- [ ] T009 [US2] Implementar inicio/cierre, ubicación previa, taller, resultado e interrupción en backend/inventory/services.py.
- [ ] T010 [US2] Bloquear entrega en servicio y API si hay mantenimiento En curso en backend/inventory/services.py.
- [ ] T011 [US2] Añadir UI de taller, lista de ubicaciones históricas, confirmación y cierre en frontend/src/components/MaintenancePanel.tsx.
- [ ] T012 [US2] Probar mantenimiento preventivo Operativo, bloqueo de entrega, cierre y confirmación de ubicación en backend/inventory/tests/test_maintenance.py y frontend/src/tests/maintenance.test.tsx.

## US3 — No localizado y recuperación

- [ ] T013 [US3] Implementar snapshots y transición por pérdida/robo, incluida interrupción de mantenimiento en backend/inventory/services.py.
- [ ] T014 [US3] Implementar recuperación con condición/ubicación y mismo código en backend/inventory/services.py.
- [ ] T015 [US3] Mostrar último estado, custodio y ubicación sin presentar asignación vigente en frontend/src/components/AssetDetail.tsx.
- [ ] T016 [US3] Probar pérdida desde Disponible, Asignado y mantenimiento; recuperación e historial en backend/inventory/tests/test_incidents.py y frontend/src/tests/recovery.test.tsx.
- [ ] T017 Actualizar historial, API docs y quickstart en specs/004-novedades-mantenimiento/ y README.md.

## Dependencias

US1 y US2 dependen de fundamentos. US3 depende de LifecycleStatus y puede integrarse con el modelo de mantenimiento. Baja aprobada pertenece a 005. No hay tareas completadas.
## Trazabilidad FR → tareas

- FR-001–FR-004: T001, T006–T008
- FR-005–FR-009: T001–T005, T009–T012
- FR-010–FR-014: T001–T005, T013–T016
- FR-015–FR-016: T001–T004, T008, T012, T016
