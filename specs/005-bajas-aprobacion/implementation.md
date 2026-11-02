# Implementación 005: avance parcial

**Fecha:** 1 de noviembre de 2026. **Estado:** parcial; no declarar implementación completa.

- `backend/inventory/retirement_policy.py`: reglas puras de elegibilidad y transiciones de solicitud/decisión/reasignación/cancelación. No persisten datos ni sustituyen los servicios transaccionales.
- `backend/inventory/management/commands/deactivate_gestor.py`: desactiva cuenta Gestor sin borrar autoría; rechaza usuario inexistente, no Gestor o ya inactivo.
- `frontend/src/components/`: NormalRetirementForm, RetirementRequestForm, RetirementRequests, ReviewerAdmin y ReviewerPasswordChange. Son componentes aislados: no están conectados a rutas ni al inicio de sesión real.
- Tests aislados de dominio, tests Django de comando y pruebas de componentes. Todos los cambios se hicieron con asistencia de IA; revisión humana pendiente.

T001 y T005 cuentan con cobertura parcial; T006, T009, T010, T011, T012, T016 y T018 tienen avance de reglas/componentes, no funcionalidad integrada. Ninguna tarea se marca completa: faltan persistencia, autorización real, endpoints, migraciones, navegación y escenarios integrales.

Para usar la única función integrada, ejecutar `backend/manage.py deactivate_gestor <usuario>` desde entorno configurado. La cuenta se desactiva completa; su historial permanece.
