# Integración 005 pendiente

**Base:** origin/develop `161187c` (PR #10 integrado). Al revisar el remoto, 003 y 004 aún no estaban integrados.

- 003 debe aportar Faculty, Operador y su inicio de sesión. No se añadió un Faculty ni Operador duplicado.
- 004 debe aportar lifecycle, restricciones de custodia, incidentes y recuperación. No se añadió otra recuperación.
- Faltan modelos ReviewerProfile, DecommissionRequest/Decision/Event y migraciones sobre migraciones reales de 003/004. No se han inventado FKs ni nombres de migración futuros.
- Crear servicios transaccionales que bloqueen activo y solicitud, revaliden permisos/revisor/facultad/revisión y usen las reglas puras. El código puro no implementa bloqueo, persistencia ni autorización.
- Conectar recuperación con cancelación atómica y cambio de facultad bloqueado mientras exista solicitud; comprobar carrera recuperación/aprobación.
- Extender Movement/constraints y rectificación de 002; preservar snapshot y decisiones. Conectar login, cambio de contraseña, endpoints y listas filtradas con autorización de servidor.
- Conectar los componentes React a API real y navegación por rol; revisar payloads y validación de campos contra implementación final. Actualmente no están visibles en la aplicación ni realizan solicitudes.
- Repetir PostgreSQL, pruebas de roles/CSRF, concurrencia y frontend completo tras integración; resolver migraciones sin modificar migraciones ya aplicadas.
