# Tasks: importación CSV

## Contratos y límites
- [ ] T001 Definir plantillas versionadas y ejemplos válidos para activos/licencias.
- [ ] T002 Definir límites de bytes, filas, retención temporal y expiración de preview.
- [ ] T003 Definir validación de documentos compartidos y política para errores de unicidad concurrentes.

## Backend
- [ ] T004 Implementar parser CSV seguro y validadores reutilizados de 003/006.
- [ ] T005 Implementar vista previa completa, errores saneados y hash inmutable.
- [ ] T006 Implementar ciclo confirmación doble con usuario/estado/hash.
- [ ] T007 Aplicar activos o lotes con batch bloqueado, revalidación contra DB actual, transacción todo-o-nada e idempotencia 201 inicial/200 reintento.
- [ ] T008 Aplicar autorización, expiración, cancelación y límites técnicos.

## Frontend
- [ ] T009 Añadir descarga de plantillas, carga y vista previa completa.
- [ ] T010 Añadir errores por fila/campo y dos confirmaciones explícitas.
- [ ] T011 Mostrar resultado final y gestionar lote expirado/cancelado.

## Verificación
- [ ] T012 Probar activo y licencias, errores múltiples, duplicados y documentos compartidos.
- [ ] T013 Probar rollback integral, reintentos, concurrencia y límites excedidos.
- [ ] T014 Registrar evidencia según `validation-plan.md`.

## Trazabilidad FR → tareas

- FR-001: T001, T004, T009
- FR-002–FR-004: T004–T005, T009–T010, T012
- FR-005–FR-006: T006, T010, T012
- FR-007: T007, T013
- FR-008–FR-009: T004, T007, T012
- FR-010: T001, T004, T012
- FR-011: T006–T007, T013
- FR-012: T002, T008, T013
