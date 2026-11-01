# Tareas: fichas y adquisición

**Estado:** planificación, todas pendientes. Pruebas incluidas porque el grupo solicitó API y pruebas.

## Fase 1 — Fundamentos

- [ ] T001 Añadir casos API y de servicio para documentos de compra/donación, importes compartidos, fecha desconocida y restricciones de edición en backend/inventory/tests/test_acquisitions.py.
- [ ] T002 Añadir pruebas de permisos para administración de facultades y edición de ficha en backend/inventory/tests/test_permissions.py.
- [ ] T003 Crear Faculty, AcquisitionDocument, AcquisitionLine y modelos de auditoría en backend/inventory/models.py.
- [ ] T004 Obtener y completar manualmente con el grupo el mapeo de facultad responsable para cada activo existente; detener la migración si faltan datos verificados. Crear migración compatible, sin completar origen/facultad por suposición, en backend/inventory/migrations/.
- [ ] T005 Implementar validaciones condicionales de compra/donación y fecha desconocida en backend/inventory/serializers.py.
- [ ] T006 Implementar servicios atómicos de adquisición y actualización auditada en backend/inventory/services.py.
- [ ] T007 Añadir rutas y vistas protegidas para facultades, adquisición, edición y auditoría en backend/inventory/urls.py y backend/inventory/views.py.

## US1 — Compra compartida

- [ ] T008 [US1] Implementar creación/lectura de factura y líneas por activo; total compartido y valor individual en backend/inventory/services.py.
- [ ] T009 [US1] Implementar formularios web de compra y enlace de múltiples activos en frontend/src/components/AcquisitionForm.tsx.
- [ ] T010 [US1] Probar compra con varios activos, campos requeridos, importes y error transaccional en backend/inventory/tests/test_acquisitions.py y frontend/src/tests/acquisition.test.tsx.

## US2 — Donación compartida

- [ ] T011 [US2] Implementar respaldo textual compartido y valor por activo en backend/inventory/serializers.py y backend/inventory/services.py.
- [ ] T012 [US2] Implementar captura web de donación y valores estimados individuales en frontend/src/components/AcquisitionForm.tsx.
- [ ] T013 [US2] Probar respaldo compartido, valores separados y rechazo de campos de factura no aplicables en backend/inventory/tests/test_acquisitions.py.

## US3 — Edición y facultades

- [ ] T014 [US3] Implementar PATCH auditado de activo y custodio preservando snapshots en backend/inventory/services.py.
- [ ] T015 [US3] Implementar administración de facultades para operador y selector de facultad en frontend/src/components/FacultyManagement.tsx y frontend/src/components/Registration.tsx.
- [ ] T016 [US3] Implementar vistas web de edición y cambios históricos en frontend/src/components/AssetEditForm.tsx y frontend/src/components/History.tsx.
- [ ] T017 [US3] Probar identidad duplicada al editar, campos de estado reservados, auditoría y permisos en backend/inventory/tests/test_assets.py y frontend/src/tests/asset-edit.test.tsx.
- [ ] T018 Actualizar contratos, README y quickstart tras validación en specs/003-fichas-adquisiciones/ y README.md.

## Dependencias

T001–T007 bloquean historias. US1 y US2 dependen de entidades/servicios; US3 depende de Faculty y auditorías. Los tests corren en PostgreSQL y frontend existente. No hay tareas completadas.
## Trazabilidad FR → tareas

- FR-001: T003, T005, T014
- FR-002: T001, T006, T014, T017
- FR-003: T014, T017
- FR-004: T005, T014, T017
- FR-005: T002, T003, T007, T015
- FR-006: T003, T004, T015
- FR-007–FR-012: T001, T003–T013
- FR-013: T001, T003, T005, T006, T014, T017
- FR-014: T001, T005, T017
- FR-015: T003, T004, T006, T017
- FR-016: T002, T003, T006, T007, T015, T017
