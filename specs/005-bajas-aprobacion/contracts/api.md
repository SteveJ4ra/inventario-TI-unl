# Contratos API: bajas y aprobación

Todas las rutas usan sesión/CSRF. Las fechas y autores se asignan en servidor.

| Método/ruta | Permiso | Resultado |
|---|---|---|
| POST /api/assets/{id}/retire/ | Gestor | Baja normal con motivo, solo LOCATED/AVAILABLE/sin custodia/sin mantenimiento activo |
| POST /api/assets/{id}/retirement-requests/ | Gestor | Solicita baja de UNLOCATED con motivo y reviewer de otra facultad |
| GET /api/reviewer/retirement-requests/ | Reviewer | Solo solicitudes asignadas |
| POST /api/retirement-requests/{id}/decision/ | Reviewer asignado | Approve o reject; motivo obligatorio si reject |
| POST /api/retirement-requests/{id}/reassign/ | Operator | Reasigna pendiente a reviewer elegible y registra autoría |
| GET/POST /api/operator/reviewers/ | Operator | Lista/crea cuenta limitada con facultad y contraseña temporal |
| PATCH /api/operator/reviewers/{id}/ | Operator | Desactiva solo si solicitudes pendientes reasignadas |
| POST /api/auth/change-password/ | Usuario autenticado | Completa cambio obligatorio de contraseña temporal |
| POST /api/assets/{id}/rectify/ | Gestor | Rectifica solo la baja errónea más reciente con motivo |

La recuperación de activo No localizado cancela por transacción toda solicitud PENDING y registra motivo ASSET_RECOVERED. El reviewer solo ve código, datos relevantes, última condición/ubicación/custodio y eventos de la solicitud. Sin listado general ni campos de edición.
La ruta de cambio de facultad de 003 debe responder 409 mientras exista solicitud PENDING del activo; este bloqueo se aplica en el servicio transaccional de baja.

Rectificar baja usa el mismo payload de 002: `{movement_id, reason, expected_revision}`; el id apunta al Movement de tipo baja enlazado al evento. Revisor temporal usa sesión adaptada desde 003 y acceso limitado de contratos transversales. No enviar contraseñas temporales en respuestas.
