# Tasks: QR de activos

## Preparación
- [ ] T001 Confirmar `PUBLIC_APP_URL` por entorno y ruta canónica con despliegue.
- [ ] T002 Fijar versión compatible de Segno y documentar dependencia/licencia.

## Backend
- [ ] T003 Implementar servicio de URL QR sin usar Host no confiable.
- [ ] T004 Implementar endpoint autenticado de SVG y errores documentados.
- [ ] T005 Proteger/validar destino local de retorno tras login.

## Frontend
- [ ] T006 Añadir descarga SVG en ficha Gestor.
- [ ] T007 Añadir entrada por código que continúe tras login hasta la ficha.

## Verificación
- [ ] T008 Cubrir autorización, PII ausente, URL canónica, no encontrado y retorno post-login.
- [ ] T009 Validar manualmente escaneo y legibilidad de impresión en varios tamaños.
- [ ] T010 Registrar evidencia de aceptación según `validation-plan.md`.

## Trazabilidad FR → tareas

- FR-001–FR-002: T002–T004, T006, T008–T009
- FR-003: T005, T007–T008
- FR-004–FR-005: T004, T008
- FR-006: T001, T003, T008
- FR-007: T002–T004, T008
- FR-008: T004, T008
