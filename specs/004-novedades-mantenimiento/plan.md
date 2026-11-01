# Plan: novedades y mantenimiento

**Rama propuesta:** feature/novedades-mantenimiento
**Fecha:** 2026-11-01 | **Spec:** spec.md

## Resumen

Extender el activo con estado de localización separado de condición y asignación. Crear eventos append-only de novedad y mantenimiento con transiciones transaccionales, snapshots y bloqueos. Se reutilizan API, permisos de Gestores, UI React y PostgreSQL existentes.

## Contexto técnico

Python 3.13, Django 5.2, DRF 3.16, PostgreSQL 17; React 19, TypeScript 7 y Vitest/Testing Library según 002. Las pruebas de concurrencia se ejecutan en PostgreSQL. No se requiere nuevo servicio.

## Modelo de estado

- LifecycleStatus: LOCATED, UNLOCATED, RETIRED (RETIRED pertenece a 005, para transición completa).
- Cuando está LOCATED, assignment es Disponible/Asignado y custodian refleja la relación vigente.
- UNLOCATED no tiene custodia vigente; el evento conserva el último assignment/custodian como snapshot.
- La condición no se borra por pérdida; se muestra como último estado conocido hasta inspección.
- Delivery requiere LOCATED, Disponible, Operativo y sin Maintenance En curso.
- Un mantenimiento activo guarda previous_location; el cierre requiere confirmed_receiving_location. UI prellena previous_location y exige confirmación, aunque se haya aceptado la sugerencia.

## Entidades y operaciones

Incident (damage/observation/lost/stolen; open/resolved/recovered/closed by approved retirement); MaintenanceEvent (in_progress/completed/interrupted); RecoveryEvent. Todo evento registra autor/timestamp de servidor y snapshots necesarios.
La condición se actualiza mediante el servicio de condición existente. El inicio/cierre de mantenimiento actualiza ubicación, pero no condición automáticamente. Una misma operación actualiza estado y evento dentro de la misma transacción.

## Secuencia técnica

1. Pruebas de transición/estado, eventos y concurrencia.
2. Añadir LifecycleStatus y modelos de eventos con migraciones que preserven activos existentes como LOCATED.
3. Servicios atómicos para novedad, iniciar/cerrar mantenimiento, no localizado y recuperación.
4. Serializadores y permisos con expected_revision; no confiar autor/fecha/custodio enviados por cliente.
5. Endpoints API; consultas de historial cronológico.
6. UI de alertas, actividad de taller, sugerencias históricas y confirmación del lugar de recepción.
7. Validación automatizada y recorrido de aceptación con datos ficticios.

## Constitution Check

Cumple trazabilidad, integridad, acceso limitado y simplicidad. Mantener estado de la constitución como propuesta; revisión contra ratificación pendiente antes de implementación. No ocultar incertidumbres institucionales como reglas verificadas.

## Contratos compartidos

Aplicar [contratos transversales](../../docs/sdd/contratos-transversales.md): sesión/roles, revisión global del activo, historial compatible, transiciones de localización y atomicidad. Esta referencia es parte del plan y de la validación de integración.
