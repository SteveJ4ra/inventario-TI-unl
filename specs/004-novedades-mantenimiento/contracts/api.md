# Contratos API: novedades y mantenimiento

Todas las mutaciones requieren Gestor activo, CSRF, expected_revision y validación en transacción.

| Método/ruta | Comportamiento |
|---|---|
| GET /api/assets/{id}/incidents/ | Lista novedades con estado/alertas |
| POST /api/assets/{id}/incidents/ | Crea daño, pérdida o robo |
| POST /api/incidents/{id}/resolve/ | Resuelve daño/observación con nota requerida |
| POST /api/assets/{id}/maintenance/ | Inicia mantenimiento con ubicación/taller y descripción |
| POST /api/maintenance/{id}/close/ | Cierra con resultado, receiving_location y location_confirmed=true |
| POST /api/assets/{id}/recover/ | Registra recuperación, condición y ubicación |
| GET /api/assets/{id}/history/ | Devuelve eventos ordenados por fecha |

En POST de pérdida/robo el backend toma snapshots, pone lifecycle_status=UNLOCATED, limpia custodia vigente y bloquea entrega. Si hay mantenimiento IN_PROGRESS lo pasa a INTERRUPTED_UNLOCATED. No acepta del cliente author, timestamp ni snapshots.
El cierre devuelve al cliente la ubicación previa para prellenar el formulario; el cliente debe confirmar una selección antes de POST. La ubicación puede ser texto nuevo.
Errores: 400 reglas/campos, 403 rol incorrecto, 404, 409 estado/revision obsoleta. Fallo no deja evento parcial.