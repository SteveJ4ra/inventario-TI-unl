# Implementación backend 005

**Estado:** backend propio implementado y probado con proveedores de contrato; activación en aplicación normal pendiente de integración 003/004. No declarar finalizado el despliegue ni todas las tareas. Alcance actual solo backend, conforme a Steven.

- retirement_models.py: ReviewerProfile, DecommissionRequest, ApprovalDecision, DecommissionEvent, RetirementAudit y ReviewerAccountAudit. FK reales y constraints de solicitud única/estado/motivo/no autoasignación.
- retirement_store.py: persistencia ORM sobre PostgreSQL, revisión global, auditoría, snapshots de nombres, baja normal/aprobada, rechazo, reasignación, cancelación y guarda de facultad pendiente para 003.
- retirement_api.py: sesión, contraseña, gestión de revisores, solicitud, listado limitado, decisión, reasignación y baja normal.
- retirement_schema.py: triggers de inmutabilidad ante SQL directo para evidencia 005. Debe invocarse en migración final tras crear tablas.
- services.py/models.py: tipo Movement baja y rectificación de su snapshot lifecycle con revisión global; se conservan original/solicitud/decisión. Migración ejecutable 0003_retirement_movement_type añade el tipo sin depender de 003/004.
- deactivate_gestor sigue integrado en la aplicación normal, con pruebas de autoría/sesión.
- Políticas, validadores y permisos preparados previamente se reutilizan en este backend.

No se registra retirement_models.py ni retirement_api.py en la configuración normal mientras falten Faculty/lifecycle reales; los tests de contrato los registran con proveedores solo de prueba. No hay fakes de producción. Todos los cambios contaron con asistencia de IA; revisión humana pendiente.

Las tareas frontend se pospusieron por instrucción de Steven. La entrega aún requiere migración del resto del esquema, conexión con los proveedores reales, montaje productivo de URL/sesión y nueva validación antes de marcar tareas completas. No publicar PR sin autorización expresa.
