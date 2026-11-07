# Modelo de datos: novedades y mantenimiento

## Asset lifecycle

- lifecycle_status: LOCATED, UNLOCATED, RETIRED (RETIRED se completa en 005).
- Condition y assignment siguen separados.
- current_custodian solo representa custodia vigente. En UNLOCATED debe ser nulo; el último custodio se guarda en evento/snapshot.
- revision aumenta con cada operación de estado.

## Incident

- asset, type (DAMAGE_OBSERVATION, LOST, STOLEN), description, status, reported_by, reported_at.
- last_condition, last_assignment, last_custodian_snapshot, last_location, active_maintenance_snapshot.
- resolution_note, resolved_by, resolved_at cuando se resuelve.
- Pérdida/robo no se resuelve como daño; se completa por RecoveryEvent o por la baja aprobada de 005.

## MaintenanceEvent

- asset, description, status (IN_PROGRESS, COMPLETED, INTERRUPTED_UNLOCATED).
- started_by/started_at, workshop_location, previous_location.
- closed_by/closed_at, result, receiving_location, location_confirmed.
- Un asset admite como máximo un evento IN_PROGRESS.

## RecoveryEvent

- incident, asset, found_at, found_by, inspected_condition, recovered_location, note.
- Cierra la situación UNLOCATED y deja asset LOCATED/Disponible/sin custodio.
- Si mantenimiento fue interrumpido, no lo reactiva.

## Migración de la restricción de custodia

Aplicar la invariante de contratos transversales: localizado permite disponible/null o asignado/custodio; No localizado/Baja exige assignment=null y current_custodian=null. Reemplazar el CheckConstraint de 002 y ampliar snapshots con lifecycle_status. Todos los eventos de activo incrementan su revisión aunque no sean Movement, para impedir rectificaciones antiguas.
