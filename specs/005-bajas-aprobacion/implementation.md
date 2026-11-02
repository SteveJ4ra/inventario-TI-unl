# Implementación 005: avance parcial

**Fecha:** 1 de noviembre de 2026. **Estado:** parcial; no declarar implementación completa.

- `backend/inventory/retirement_workflow.py`: orquestación sobre el protocolo RetirementStore para baja, solicitud, decisión y reasignación; exige autorización, revisión y bloqueo de activo antes de solicitud. No tiene adaptador ORM ni rutas activas.
- `backend/inventory/retirement_policy.py`: reglas puras de elegibilidad y transiciones de solicitud/decisión/reasignación/cancelación. No persisten datos ni sustituyen los servicios transaccionales.
- `backend/inventory/management/commands/deactivate_gestor.py`: desactiva cuenta Gestor sin borrar autoría; rechaza usuario inexistente, no Gestor o ya inactivo.
- `backend/inventory/retirement_serializers.py` y `retirement_permissions.py`: validación estricta de entradas y permisos de revisor preparados; todavía no están conectados a endpoints ni a un modelo ReviewerProfile real. La interfaz se retiró por decisión de alcance actual: solo backend.
- Tests aislados de dominio y pruebas Django del comando, serializadores y permisos. Todos los cambios se hicieron con asistencia de IA; revisión humana pendiente.

T001, T004 y T005 cuentan con cobertura parcial; T006, T009, T010 y T014 tienen avance de reglas/validadores, no funcionalidad integrada. Las tareas de interfaz se posponen por el alcance backend solicitado. Ninguna tarea se marca completa: faltan persistencia, autorización real, endpoints, migraciones y escenarios integrales de backend.

Para usar la única función integrada, ejecutar `backend/manage.py deactivate_gestor <usuario>` desde entorno configurado. La cuenta se desactiva completa; su historial permanece.

## Correcciones de revisión

Se añadieron validaciones explícitas de identidad/revisión/banderas/snapshots en dominio y orquestación; permisos exigen perfil del mismo usuario y bandera de contraseña exactamente False; username usa validador Django. Regresiones y pendientes por FR en review.md. Solo cambios locales de revisión hasta nueva autorización de publicación.
