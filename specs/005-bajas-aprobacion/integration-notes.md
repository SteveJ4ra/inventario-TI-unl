# Integración 005 pendiente

**Base:** origin/develop `161187c` (PR #10 integrado). Al revisar el remoto, 003 y 004 aún no estaban integrados.

- 003 debe aportar Faculty, Operador y su inicio de sesión. No se añadió un Faculty ni Operador duplicado.
- 004 debe aportar lifecycle, restricciones de custodia, incidentes y recuperación. No se añadió otra recuperación.
- Faltan modelos ReviewerProfile, DecommissionRequest/Decision/Event y migraciones sobre migraciones reales de 003/004. No se han inventado FKs ni nombres de migración futuros.
- Implementar adaptador ORM de RetirementStore en retirement_workflow.py: atomic real, bloqueo de activo antes de solicitud, acceso seguro al perfil revisor, comprobación de roles/cambio de contraseña, snapshots, registros append-only y revisión. El puerto y sus tests con dobles no implementan ni prueban bloqueo, persistencia ni autorización reales. Conectar las rutas al adaptador solo al verificarlo en PostgreSQL.
- Conectar recuperación con cancelación atómica y cambio de facultad bloqueado mientras exista solicitud; comprobar carrera recuperación/aprobación.
- Extender Movement/constraints y rectificación de 002; preservar snapshot y decisiones. Conectar login, cambio de contraseña, endpoints y listas filtradas con autorización de servidor.
- Conectar los validadores y permisos 005 a endpoints reales y al perfil revisor de 003/005; verificar filtrado de solicitudes por usuario en la base de datos y cambio inicial de contraseña. El frontend queda fuera del alcance actual.
- Repetir PostgreSQL, pruebas backend de roles/CSRF y concurrencia tras integración; resolver migraciones sin modificar migraciones ya aplicadas.

## Contratos precisados por revisión

ReviewerProfile debe exponer `user_id`, `faculty_id` y `must_change_password` booleano no nulo, con relación `user.reviewer_profile`. El permiso preparado usa el grupo técnico `Revisores`; acordar esa constante al conectar provisión y login. Guardas globales deben impedir que una cuenta temporal con otros grupos eluda el cambio inicial. El adaptador debe proteger revisor/rol frente a cambios concurrentes; los tests actuales no certifican esa protección. Ver review.md antes de declarar completa cualquier tarea.

La orquestación incluye cancel_for_recovery, que exige actor Gestor, revisión y recovery_event_id. El adaptador debe usar atomic anidado en la misma conexión y el servicio de 004 debe invocarlo dentro de la transacción exterior; aún no se ha probado rollback real.

El adaptador de recuperación debe verificar que recovery_event_id pertenezca al activo bloqueado; si no coincide, rechazar sin cancelación. Esta validación aislada no reemplaza la restricción/integración ORM real.
