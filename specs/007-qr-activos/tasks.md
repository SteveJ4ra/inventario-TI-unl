# Tasks: QR de activos

> **Estado revisado el 2026-11-04.** Casillas `[x]` solo para implementación con evidencia. Tareas con validaciones o decisiones funcionales pendientes permanecen `[ ]`. No equivale a aceptación global ni merge.

## Preparación
- [ ] T001 Confirmar `PUBLIC_APP_URL` por entorno y ruta canónica con despliegue.
- [x] T002 Fijar versión compatible de Segno y documentar dependencia/licencia.

## Backend
- [x] T003 Implementar servicio de URL QR sin usar Host no confiable.
- [x] T004 Implementar endpoint autenticado de SVG, resolución exacta por código TI y errores documentados en backend/inventory/views.py y urls.py.
- [x] T005 Proteger/validar destino local de retorno tras login.

## Frontend
- [x] T006 Añadir descarga SVG en ficha Gestor.
- [x] T007 Añadir entrada por código que continúe tras login hasta la ficha.

## Verificación
- [x] T008 Cubrir autorización, PII ausente, URL canónica, no encontrado y retorno post-login.
- [ ] T009 Validar manualmente escaneo y legibilidad de impresión en varios tamaños.
- [ ] T010 Registrar evidencia de aceptación según `validation-plan.md`.

## Trazabilidad FR → tareas

- FR-001–FR-002: T002–T004, T006, T008–T009
- FR-003: T005, T007–T008
- FR-004–FR-005: T004, T008
- FR-006: T001, T003, T008
- FR-007: T002–T004, T008
- FR-008: T004, T008

## Evidencia y pendientes por tarea

- **T001**: la URL local `http://127.0.0.1:5173` carga en Django. Falta acuerdo HTTPS del despliegue y accesibilidad desde un escáner externo. `backend/.env.example` ya documenta la variable.
- **T002**: Segno `1.6.6` en dependencias; licencia BSD documentada en `implementation.md`.
- **T003**: `qr_urls.py` probado; test de `Host` alternativo PASS.
- **T004**: endpoints y permisos API probados; 10 tests QR backend PASS, más suite de 55 PASS.
- **T005**: el alumno confirmó prueba manual en ventana sin sesión → login → ficha del mismo `TI-000001`; ruta interna conservada. El backend verifica el Host alternativo. No se ha realizado prueba adicional manual de redirección externa (no se añadió una funcionalidad de `next`).
- **T006**: botón web descargó SVG real.
- **T007**: enlace con Gestor autenticado abrió ficha `TI-000001` y el alumno confirmó retorno a la misma ficha después del login.
- **T008**: 10/10 QR backend, 55/55 suite backend total y 5 pruebas frontend QR aprobadas; 25/25 frontend total. La suite backend total incluye los 10 casos QR (no sumar dos veces).
- **T009**: el teléfono reconoció el enlace QR; el alumno confirmó que el resto de la verificación manual cumple, incluida legibilidad. La apertura remota no se pudo realizar porque el QR contiene `127.0.0.1`; falta URL de despliegue accesible y registro preciso de tamaños/dispositivo para cerrar esta tarea sin reservas.
- **T010**: documentación actualizada con resultados posteriores: Python 3.13.17 disponible, frontend 25/25, confirmación de flujo post-login y reconocimiento en teléfono. Quedan URL de despliegue, detalles de impresión, auditoría e integración/revisión humana.
