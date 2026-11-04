# Tareas: licencias

**Estado:** T001–T013 implementadas y comprobadas localmente; actualización de seguridad DRF 3.18.2 aplicada y comprobada; revisión humana pendiente. Evidencia: [validation.md](validation.md) y [reviews.md](reviews.md).

## US1 — Crear y consultar lotes

- [x] T001 Probar altas, fechas, cantidades, estados y permisos en backend/inventory/tests/test_license_lots.py.
- [x] T002 Crear SoftwareLicenseLot y LicenseLotAudit con constraints en backend/inventory/models.py.
- [x] T003 Crear migraciones en backend/inventory/migrations/.
- [x] T004 Implementar serializadores y cálculos derivados en backend/inventory/serializers.py.
- [x] T005 Implementar servicios y validación de revision en backend/inventory/services.py.
- [x] T006 Implementar listado/detalle/alta/edición en backend/inventory/views.py y backend/inventory/urls.py.
- [x] T007 Crear formulario/listado web en frontend/src/components/LicenseLots.tsx.

## US2 — Actualizar uso y vigencia

- [x] T008 [US2] Registrar before/after, autor y fecha ante cambios de cantidades en backend/inventory/services.py.
- [x] T009 [US2] Mostrar remanentes, estado temporal e historial en frontend/src/components/LicenseLotDetail.tsx.
- [x] T010 [US2] Probar límites, cambios concurrentes y lotes vencidos en backend/inventory/tests/test_license_lots.py.
- [x] T011 [US2] Probar UI, errores de validación y etiquetas de estado en frontend/src/tests/license-lots.test.tsx.

## Polishing

- [x] T012 Actualizar documentación, contrato y guía de ejecución en specs/006-lotes-licencias/ y README.md.
- [x] T013 Revisar que claves o asociaciones individuales no aparezcan en API ni UI en backend/inventory/serializers.py y frontend/src/components/LicenseLots.tsx.

## Dependencias

No depende de 003–005; requiere autenticación de Gestor de 002. Importación CSV de lotes pertenece a 008. Las trece tareas tienen implementación y evidencia local; esto no equivale a aprobación humana o validación global.
## Trazabilidad FR → tareas

- FR-001–FR-002: T001–T007
- FR-003–FR-007: T001–T006, T008–T010
- FR-008–FR-010: T001, T004–T006, T008–T011
- FR-011–FR-012: T006–T007, T010–T013
