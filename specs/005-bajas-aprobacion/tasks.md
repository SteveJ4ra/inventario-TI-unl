# Tareas: bajas y aprobación independiente

**Estado:** todas pendientes; pruebas planificadas.

## Base

- [ ] T001 Probar baja normal, baja No localizado, aprobación, rechazo, cancelación por recuperación y permisos en backend/inventory/tests/test_decommission.py.
- [ ] T002 Añadir DecommissionRequest, ApprovalDecision, ReviewerProfile y restricciones de estado en backend/inventory/models.py.
- [ ] T003 Implementar servicios transaccionales y snapshots de baja/solicitud/decisión en backend/inventory/services.py.
- [ ] T004 Añadir permisos Operator y Reviewer sin conceder acceso global de Gestor en backend/inventory/permissions.py.
- [ ] T005 Crear comando local para provisionar el primer operador técnico y comando deactivate_gestor; probar ambos en backend/inventory/management/commands/ y backend/inventory/tests/test_manager_command.py.

## US1 — Bajas normales

- [ ] T006 [US1] Implementar validación de estado, motivo y baja terminal en backend/inventory/services.py.
- [ ] T007 [US1] Añadir acción baja normal y motivo en frontend/src/components/AssetDetail.tsx.
- [ ] T008 [US1] Probar requisito de cerrar mantenimiento, motivo, no aprobación y conservación de historial en backend/inventory/tests/test_decommission.py.

## US2 — Solicitud/decisión

- [ ] T009 [US2] Implementar elegibilidad de reviewer por facultad, no autoaprobación y bloqueo de cambio de facultad mientras la solicitud esté PENDING en backend/inventory/services.py.
- [ ] T010 [US2] Implementar decisión/rechazo, nueva solicitud tras rechazo y cancelación por recuperación con motivo en backend/inventory/services.py.
- [ ] T011 [US2] Crear bandeja de solicitudes para Gestor/reviewer con datos mínimos en frontend/src/components/RetirementRequests.tsx.
- [ ] T012 [US2] Añadir formularios de solicitud, aprobación/rechazo y motivo obligatorio en frontend/src/components/RetirementRequestForm.tsx.
- [ ] T013 [US2] Probar filtrado por asignación, facultad, rechazo, re-solicitud y cancelación por recuperación en backend/inventory/tests/test_decommission.py y frontend/src/tests/retirement.test.tsx.

## US3 — Administración de revisor

- [ ] T014 [US3] Implementar creación de reviewer con contraseña temporal, faculty y must_change_password en backend/inventory/serializers.py y backend/inventory/services.py.
- [ ] T015 [US3] Implementar cambio obligatorio de contraseña inicial en backend/inventory/auth_views.py.
- [ ] T016 [US3] Implementar UI de operador para crear/desactivar/reasignar revisores en frontend/src/components/ReviewerAdmin.tsx.
- [ ] T017 [US3] Impedir desactivación con pending sin reasignación y probar en backend/inventory/tests/test_permissions.py.
- [ ] T018 [US3] Actualizar cliente de sesión para roles operador/revisor y cambio inicial de contraseña en frontend/src/api.ts y frontend/src/App.tsx.
- [ ] T019 Actualizar contratos, documentación y quickstart en specs/005-bajas-aprobacion/ y README.md.

## Dependencias

005 requiere Faculty de 003 y UNLOCATED/Recovery de 004. En producción del grupo, revisar 003/004 en develop antes de implementar. No hay tareas completadas.
## Trazabilidad FR → tareas

- FR-001–FR-004: T001–T008
- FR-005–FR-010: T001, T003, T009–T013
- FR-011–FR-013: T004, T014–T018
- FR-014: T005, T018
- FR-015–FR-017: T001, T003, T006, T008–T010, T013
