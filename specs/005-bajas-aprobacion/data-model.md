# Modelo de datos: bajas y aprobación

## DecommissionEvent

- asset, type NORMAL/APPROVED_UNLOCATED, reason, actor, occurred_at.
- Original inmutable y relacionado con estado previo/snapshot.

## DecommissionRequest

- asset No localizado; requester; requested_at; reason; assigned_reviewer; status.
- Una solicitud PENDING por activo.
- Rechazo permite nueva solicitud sin sobrescribir anterior.
- Recuperación cancela solicitud pendiente con reason_code ASSET_RECOVERED, actor system y recovery_event_id.

## ApprovalDecision

- request, reviewer, decision APPROVE/REJECT, reason required on REJECT, decided_at.
- Solo reviewer asignado puede decidir una vez; no autoaprobación ni misma facultad.
- Las decisiones previas se preservan al reasignar solicitud pendiente.

## ReviewerAccount

- Django User individual; active; faculty FK; must_change_password.
- Privilegio limitado al endpoint de solicitudes asignadas.
- Desactivación requiere cero solicitudes pendientes asignadas.
- Cuenta Operator separada administra revisores; no tiene permiso implícito de Gestor.

## Gestor lifecycle

- Comando deactivate_gestor cambia is_active; no borra ni altera eventos creados.
- Auth rechaza usuario inactivo.
Cada reasignación registra operador autor, fecha/hora, revisor anterior y revisor nuevo; Gestores no tienen permiso para ejecutar la operación.

## Rectificación compatible con 002

Cada DecommissionEvent enlaza uno a uno un Movement de tipo nuevo `baja`; ampliar choices y constraints del Movement de 002. El movimiento contiene before/after completos, lifecycle y resulting_revision. `/rectify/` conserva entrada `movement_id`, `reason`, `expected_revision` y enlace rectifies de 002. Solo la baja cuya revisión sigue siendo la actual puede rectificarse; restaura snapshot previo sin borrar aprobación/solicitud ni reabrirla como pendiente. Una baja aprobada rectificada deja No localizado, con los antecedentes originales conservados. No rectificar una rectificación ni reactivar movimientos antiguos.
