# Especificación: bajas y aprobación independiente

**Rama propuesta:** feature/bajas-aprobacion
**Identificador:** 005-bajas-aprobacion
**Creado:** 1 de noviembre de 2026
**Estado:** especificación preparada; no implementada.
**Decisiones:** DBE-022 a DBE-029 y aclaraciones posteriores en ../../docs/sdd/decisiones-alcance-backend.md.

## Descripción

Retirar activos sin borrar su ficha ni historial. Las bajas normales se registran por gestores cuando el activo está localizado, Disponible, sin custodio y sin mantenimiento activo. Para un activo No localizado, un gestor presenta una solicitud con motivo y una persona revisora de otra facultad decide aprobarla o rechazarla. El revisor tiene permiso limitado a sus solicitudes.

## Historias y aceptación

### US1 — Dar de baja un activo localizado (P1)

Como gestor, quiero registrar una baja con motivo para conservar evidencia de por qué el activo deja de formar parte del inventario disponible.

1. El activo debe estar localizado, Disponible, sin custodio vigente y sin mantenimiento En curso.
2. Se permite cualquier condición, por ejemplo Averiado, En reparación después de cerrar su mantenimiento, u Operativo por obsolescencia.
3. Motivo obligatorio, autor y fecha/hora automáticos.
4. La ficha e historial permanecen; el estado pasa a Baja y el código no se reutiliza.
5. La operación no requiere aprobación independiente.

### US2 — Solicitar y resolver una baja de No localizado (P1)

Como gestor, quiero solicitar baja de un activo No localizado y que una persona de otra facultad tome una decisión separada.

1. Solicitud con motivo obligatorio, autor, fecha y revisor activo de otra facultad.
2. No puede aprobar el mismo usuario que solicitó.
3. El revisor ve únicamente sus solicitudes y los datos de activo necesarios para decidir, incluido último estado/custodio/condición/ubicación conocidos.
4. Rechazar exige motivo; el activo permanece No localizado.
5. Tras rechazo, un gestor puede crear otra solicitud con motivo actualizado.
6. Aprobar registra la baja, con revisor y fecha/hora.
7. Si el activo se recupera antes de la decisión, el sistema cancela la solicitud con motivo de cancelación “activo recuperado”, vínculo al evento de recuperación y fecha/hora; el activo sigue el flujo de recuperación.
8. Si el revisor queda inactivo con solicitudes pendientes, solo el operador puede reasignarlas a revisores elegibles antes de desactivarlo; se registra quién realizó cada reasignación.

### US3 — Administrar revisores y facultades (P1)

Como operador técnico autorizado, quiero crear/desactivar cuentas revisoras y mantener su facultad para que la revisión sea individual y ajena a la facultad del activo.

1. No existe auto-registro público de revisores.
2. El operador crea cuenta individual con facultad y contraseña temporal.
3. El revisor debe cambiar la contraseña en el primer acceso.
4. La cuenta no puede editar activos ni ejecutar operaciones de gestor; solo puede ver solicitudes asignadas y aprobar/rechazar.
5. La desactivación impide autenticación y requiere que el operador reasigne antes las solicitudes pendientes; la reasignación conserva su autoría.
6. La lista de facultades es manual y la administra el operador; sus valores son identidades controladas del incremento 003.

### US4 — Desactivar una cuenta gestora (P2)

Como operador del proyecto, quiero desactivar una cuenta gestora que ya no debe acceder, conservando su autoría histórica.

1. Alta/baja gestora ocurre mediante comandos locales; no se agrega API de administración ni registro público.
2. Desactivar una cuenta no borra sus eventos ni reescribe autores.
3. El usuario inactivo no puede iniciar sesión ni ejecutar operaciones.

## Requisitos funcionales

- FR-001: Permitir baja normal solo para activo localizado, Disponible, sin custodio vigente y sin mantenimiento En Curso.
- FR-002: Permitir baja normal bajo cualquier condición; exigir motivo y guardar autor/fecha.
- FR-003: Antes de la baja normal de un activo en mantenimiento, exigir cierre del mantenimiento con resultado.
- FR-004: Conservar ficha, historial y código; no borrar activo ni reutilizar su identificador.
- FR-005: Permitir solicitar baja solo a activo No localizado, con motivo, usuario Gestor, fecha y revisor asignado.
- FR-006: Rechazar autoaprobación y revisores cuya facultad sea igual a la responsable del activo.
- FR-007: Limitar cada revisor a solicitudes asignadas y datos del activo necesarios para decidir; no conceder acceso de edición/inventario.
- FR-008: Aprobar baja No localizado mediante decisión inmutable con autor/fecha; al aprobar el activo pasa a Baja.
- FR-009: Rechazar solicitud con motivo obligatorio; el activo continúa No localizado y admite nueva solicitud con motivo actualizado.
- FR-010: Cancelar automáticamente solicitud pendiente si el activo se recupera; guardar motivo, autor del evento automático, fecha y vínculo a recuperación.
- FR-011: Solo el operador puede reasignar una solicitud pendiente a otro revisor elegible; impedir desactivar revisor hasta que el operador reasigne todas las pendientes.
- FR-012: Operador técnico autorizado puede crear/desactivar revisores desde la interfaz y asignar facultad.
- FR-013: El primer inicio de sesión del revisor exige cambiar la contraseña temporal.
- FR-014: Alta/baja de gestores permanece por comandos locales; usuario inactivo no accede y la autoría histórica se conserva.
- FR-015: Permitir rectificar una baja errónea solo si es el error más reciente, con motivo y vínculo, preservando baja original.
- FR-016: Mantener los datos e historial sin borrado automático.
- FR-017: Rechazar el cambio de facultad responsable mientras exista solicitud de baja pendiente; la autorización y auditoría del cambio corresponden a 003.

## Criterios de éxito

- SC-001: Baja normal solo ocurre desde estado elegible, con motivo/autor/fecha, sin aprobación adicional.
- SC-002: Una solicitud de No localizado no se aprueba por el solicitante ni por alguien de la misma facultad del activo.
- SC-003: Un revisor no puede consultar inventario general ni modificar activo.
- SC-004: Rechazo exige motivo y permite una nueva solicitud; recuperación cancela automáticamente la pendiente con causa auditable.
- SC-005: No se desactiva revisor si quedan solicitudes sin reasignar.
- SC-006: Una baja aprobada conserva la ficha, movimientos, solicitud y decisión.
- SC-007: Mientras una solicitud esté pendiente, el endpoint de cambio de facultad responde conflicto y conserva la facultad usada para elegir revisor.
- SC-008: Un Gestor no puede reasignar solicitudes; el operador sí puede reasignar a otro revisor elegible, y la reasignación queda atribuida al operador.
