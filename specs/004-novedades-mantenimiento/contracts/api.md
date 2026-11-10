# Contratos API: novedades y mantenimiento

Todas las mutaciones requieren Gestor activo, CSRF, expected_revision y validación en transacción.

| Método/ruta | Comportamiento |
|---|---|
| GET /api/assets/{id}/incidents/ | 200. Lista novedades, estado, autoría y fechas. |
| POST /api/assets/{id}/incidents/ | 201. Crea una novedad con `type` (`damage`, `observation`, `lost` o `stolen`) y `description`. |
| POST /api/incidents/{id}/resolve/ | 200. Resuelve daño u observación pendiente con `resolution_note`. |
| POST /api/assets/{id}/maintenance/ | 201. Inicia mantenimiento con `workshop_location` y `description`. |
| GET /api/maintenance/{id}/ | 200. Devuelve el detalle, `previous_location` y la revisión vigente. |
| POST /api/maintenance/{id}/close/ | 200. Cierra con `result`, `receiving_location` y `location_confirmed: true`. |
| POST /api/assets/{id}/recover/ | 201. Registra recuperación con `inspection_confirmed: true`, `inspected_condition`, `recovered_location` y `note` opcional. |
| GET /api/assets/{id}/history/ | 200. Historial unificado ordenado por revisión descendente, con fecha, tipo e ID como desempate. |

En POST de pérdida/robo el backend toma snapshots, pone lifecycle_status=UNLOCATED, limpia custodia vigente y bloquea entrega. Si hay mantenimiento IN_PROGRESS lo pasa a INTERRUPTED_UNLOCATED. No acepta del cliente author, timestamp ni snapshots.
GET /api/maintenance/{id}/ devuelve detalle, previous_location y revisión vigente antes del cierre para prellenar el formulario; el cliente confirma receiving_location y location_confirmed antes de POST. La ubicación puede ser texto nuevo.
Errores: 400 reglas/campos, 403 rol incorrecto, 404, 409 estado/revision obsoleta. Fallo no deja evento parcial.

En respuestas de activo UNLOCATED, assignment y current_custodian son null; last_assignment/custodian provienen del snapshot. Entrega/devolución/condición no pueden tratar este activo como localizado. Historial integrado y rectificación siguen el contrato transversal.

La ficha identifica el mantenimiento en curso con `active_maintenance_id`. Para un activo No localizado devuelve además `last_lifecycle_status`, `last_assignment`, `last_condition`, `last_location` y `last_custodian`. La última custodia proviene del reporte, sin consultar al custodio vigente.

El orden del historial sigue [el contrato transversal](../../../docs/sdd/contratos-transversales.md#revisión-historial-y-rectificación). Esto precisa la redacción anterior que mencionaba solo la fecha. Cada entrada contiene `event_type`, `event_id`, `occurred_at`, `actor`, `resulting_revision` y `data`. La evidencia de 004 incluye `projection_id`, `before` y `after`. El historial de 002 sigue disponible en `/movements/` con su formato original.
