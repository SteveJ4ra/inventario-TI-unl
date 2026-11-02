# Revisión final del avance backend 005

**Fecha:** 1 de noviembre de 2026. **Resultado:** correcciones del avance verificadas; feature completa NO lista para PR de entrega terminada. Sin publicación ni reapertura de PR durante esta revisión.

## Hallazgos y resolución

| Hallazgo | Corrección / estado |
|---|---|
| Estado de contraseña null/0/vacío podía habilitar permisos por negación booleana | Solo `must_change_password is False` permite acceso a solicitudes; regresión agregada. |
| Perfil revisor no comprobaba pertenencia al usuario ni identidad/facultad válida | Se exige usuario persistido, faculty_id positivo y profile.user_id correspondiente. Es un contrato preparado, no conexión con modelo real. |
| Adaptador podía devolver otro activo o solicitud y aun así avanzar | Se comprueban identidades devueltas antes de escribir, además de la identidad del revisor. |
| Python permite True como entero y otros datos ambiguos en funciones internas | Actor, IDs y revisión se validan estrictamente; banderas de estado deben ser booleanas, motivo limitado a 2000 como en API. |
| Snapshot No localizado podía conservar custodia o mantenimiento activo | Se rechaza el snapshot incoherente antes de crear/decidir/reasignar; exige facultad válida. |
| Username aceptaba caracteres incompatibles con reglas de Django | Se reutiliza UnicodeUsernameValidator. |
| Evidencia acumulaba conteos históricos y no resumía la versión revisada | validation.md actualizado con comandos, resultado real y límites actuales. |
| Faltan modelos, migraciones, rutas y adaptador ORM reales | PENDIENTE. No se oculta con dobles de producción ni se declara validación integral. |

Los casos de regresión reprodujeron fallos antes de las correcciones. Las pruebas de permiso/serialización son aisladas; solo el comando de desactivación está conectado a persistencia real de 002.

## Revisión por requisito de 005

| Requisito | Evidencia actual y pendiente |
|---|---|
| FR-001–003 | Elegibilidad de baja normal comprobada en dominio; no existe operación persistente/endpoints de baja. |
| FR-004 | 002 conserva registro/historial y el comando conserva autores; falta estado/evento de baja. |
| FR-005 | Regla de No localizado y solicitud única comprobada con puerto de pruebas; falta constraint SQL/alta real. |
| FR-006 | Independencia y facultades validadas en dominio; falta revalidación bajo bloqueos de DB reales. |
| FR-007 | Clase de permiso por objeto preparada; falta queryset filtrado y prueba API de acceso real. |
| FR-008–009 | Reglas aprobar/rechazar y nota requeridas probadas; sin decisión persistida ni nueva solicitud real posterior. |
| FR-010 | Política de cancelación conserva causa; falta enlace a recuperación/evento y transacción de 004. |
| FR-011 | Reasignación restringida en dominio; falta desactivación real de revisor y bloqueo por solicitudes SQL. |
| FR-012 | Validadores de creación/desactivación preparados; no hay provisión de revisor ni autorización de Operador real. |
| FR-013 | Permiso deniega estado temporal/desconocido; falta login, cambio validado con Django y guardas globales de sesión. |
| FR-014 | deactivate_gestor probado con PostgreSQL: sesión/inicio denegados y autores conservados; create_gestor permanece en 002. |
| FR-015 | Rectificación de baja NO implementada; falta enlace DecommissionEvent/Movement y revisión global integrada. |
| FR-016 | Protección de historial existente permanece; eventos 005 aún no existen y no se verificó su conservación. |
| FR-017 | Cambio de facultad bloqueado por solicitud pendiente NO integrado con 003. |

## Pruebas y límites

19 tests aislados de dominio/orquestación PASS; 44 tests de suite backend PASS bajo runner PostgreSQL temporal; pip check PASS; diff sin errores de whitespace. No se probaron concurrencia real, rollback, idempotencia de decisiones ni permisos HTTP de los endpoints 005 porque esos endpoints/adaptador/modelos no existen. Los tests con Store en memoria comprueban guardas y orden de llamadas, NO bloqueos ni atomicidad SQL.

La aprobación para publicar un PR queda reservada a Steven. El PR anterior fue cerrado y esta revisión no lo reabre. Se necesita completar modelos/migraciones/servicios/API y después ejecutar los escenarios pendientes de validation-plan.md; no basta con integrar proveedores y asumir que el resto aparecerá automáticamente.
