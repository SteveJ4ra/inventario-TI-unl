# Tasks: importación CSV

## Contratos y límites
- [x] T001 Definir plantillas versionadas y ejemplos válidos para activos/licencias.
- [x] T002 Definir límites de bytes, filas, retención temporal y expiración de preview.
- [x] T003 Definir validación de documentos compartidos y política para errores de unicidad concurrentes.

## Backend
- [ ] T004 Implementar parser CSV seguro y validadores reutilizados de 003/006.
  - Parser y validación CSV completos; reutilización de validadores 003/006 pendiente de integración.
- [x] T005 Implementar vista previa completa, errores saneados y hash inmutable.
- [x] T006 Implementar ciclo confirmación doble con usuario/estado/hash.
- [ ] T007 Aplicar activos o lotes con batch bloqueado, revalidación contra DB actual, transacción todo-o-nada e idempotencia 201 inicial/200 reintento.
  - Orquestación, bloqueo, revalidación, rollback lógico e idempotencia probados con fake; transacción real de dominio pendiente de 003/006.
- [x] T008 Aplicar autorización, expiración, cancelación y límites técnicos.

## Frontend
- [x] T009 Añadir descarga de plantillas, carga y vista previa completa.
- [x] T010 Añadir errores por fila/campo y dos confirmaciones explícitas.
- [x] T011 Mostrar resultado final y gestionar lote expirado/cancelado.

## Verificación
- [x] T012 Probar activo y licencias, errores múltiples, duplicados y documentos compartidos.
- [x] T013 Probar rollback integral, reintentos, concurrencia y límites excedidos.
- [x] T014 Registrar evidencia según `validation-plan.md`.

## Trazabilidad FR → tareas

- FR-001: T001, T004, T009
- FR-002–FR-004: T004–T005, T009–T010, T012
- FR-005–FR-006: T006, T010, T012
- FR-007: T007, T013
- FR-008–FR-009: T004, T007, T012
- FR-010: T001, T004, T012
- FR-011: T006–T007, T013
- FR-012: T002, T008, T013
