# Alcance SDD del backend — Inventario TI

**Fecha de consolidación:** 1 de noviembre de 2026
**Fuente funcional:** respuestas de Steven en esta conversación y decisiones previas de 002.
**Estado:** alcance confirmado por el responsable del proyecto para preparación SDD; falta revisión/ratificación del equipo e implementación futura.

## Propósito y límite

Preparar el backend del proyecto de Inventario de TI a partir del tema 2 del banco de proyectos: mantener información actual de activos tecnológicos y parte de su historial de ciclo de vida. El alcance evita inventar procesos institucionales que el grupo no conoce. No se integra con sistemas de la UNL ni se declara que estas reglas sean política institucional.

El incremento 002 contiene la base de registro, consulta, búsqueda, filtros, custodios, entregas, devoluciones, cambios de condición y rectificación. Su PR #9 está integrado en develop (02cb26c); estos documentos planifican incrementos posteriores sin fusionarlo ni modificar el estado remoto. La existencia de artefactos SDD no significa que 003–008 estén implementados o validados.

## Incrementos planificados

| ID | Incremento | Resultado | Dependencias |
|---|---|---|---|
| 003 | Fichas, facultades y adquisición | Editar activos/custodios con auditoría; facultad responsable; documentos compartidos de compra o donación. | 002 |
| 004 | Novedades, pérdida y mantenimiento | Registrar observaciones, daños, pérdida/robo, recuperación y mantenimiento en curso/cierre. | 002; 003 para facultad no es necesaria |
| 005 | Baja y aprobación independiente | Bajas normales; solicitud y aprobación de baja de No localizados; cuentas revisoras limitadas y su administración. | 003, 004 |
| 006 | Lotes de licencias | Control agregado de puestos finitos, inicio obligatorio, fin opcional y remanentes calculados. | 002; independiente de 003 |
| 007 | QR de activos | Enlace QR descargable que abre la ficha tras autenticación. | 002 |
| 008 | Importación CSV | Importación atómica, con vista previa y dos confirmaciones, de activos y lotes de licencias. | 003, 006 |

003, 004, 006 y 007 pueden prepararse en paralelo una vez disponible 002. 005 requiere estados de pérdida/recuperación y datos de facultad. 008 requiere estabilizar los modelos de activos, adquisición y licencias.

## Capacidades incluidas

1. Acceso de gestores; sus altas y bajas siguen mediante comandos locales, sin registro público.
2. Operación del inventario físico: alta existente, consulta, edición auditada, custodios, entregas/devoluciones e historial.
3. Documentar compra o donación, con documento compartido y valor individual de cada activo.
4. Novedades por daño/observación, pérdida o robo, alertas y recuperación.
5. Mantenimiento real en curso y cierre; la actividad bloquea entregas mientras esté abierta.
6. Bajas con motivo e historial. Las bajas de activos No localizados requieren aprobación de otra facultad.
7. Revisores con acceso limitado a solicitudes asignadas; operador técnico administra cuentas revisoras y facultades desde interfaz.
8. Control agregado de lotes de licencias finitas por usuario o dispositivo.
9. QR descargable para activos físicos, con autenticación al abrir el enlace.
10. CSV para activos y lotes de licencias, transaccional y con confirmación doble.

## Exclusiones confirmadas

- Traslados independientes como operación general; la ubicación se actualiza en las operaciones aprobadas (entrega, devolución, mantenimiento y recuperación).
- Integración con sistemas institucionales o identidad institucional.
- Licencias ilimitadas/de campus, claves de activación y asignación de licencias a usuarios/equipos.
- Portal de custodios, QR de licencias, captura de documentos/facturas como imágenes y agenda futura de mantenimiento.
- Selector de moneda en la interfaz. La divisa base del proyecto es USD y se centraliza en configuración para una futura modificación de código.
- Borrado físico de activos, movimientos, documentos o historial.
- Reportes financieros, contabilidad, valoración institucional y reglas legales no confirmadas.

## Ocho etapas SDD y su estado

| Etapa | Artefacto/resultado | Estado |
|---|---|---|
| 1. Constitución | .specify/memory/constitution.md | Propuesta compartida; pendiente de ratificación por el equipo. No se crea una constitución por funcionalidad. |
| 2. Specify | specs/003 a specs/008/spec.md | Preparadas con requisitos y aceptación comprobable; pendientes de revisión grupal. |
| 3. Clarify | docs/sdd/decisiones-alcance-backend.md y aclaraciones en cada spec | Respuestas del responsable registradas hasta DBE-051; revisión grupal pendiente. No equivalen a validación institucional. |
| 4. Plan | plan.md, research.md, data-model.md, contracts/, quickstart.md | Artefactos preparados para 003–008; límites técnicos pendientes donde se indica. |
| 5. Tasks | tasks.md | Tareas preparadas y sin marcar; paquetes asignados en docs/sdd/guias-integrantes/. |
| 6. Analyze | revisión de consistencia entre spec/plan/tasks | Pase cruzado realizado y registrado en `docs/sdd/analisis-cruzado.md`; se corrigieron vacíos de criterios/trazabilidad y se integraron decisiones hasta DBE-051. Revisión grupal pendiente. |
| 7. Implement | código y migraciones | Pendiente del equipo; ninguna tarea nueva se marca completada aquí. |
| 8. Validate/review | pruebas, aceptación, revisión humana y evidencia | Planeado en validation-plan.md; no ejecutado para los incrementos 003–008. |

## Preparación para iniciar implementación

Los paquetes 003–008 se conservan completos, asignados respectivamente a Alex, Yandri, Steven, Anderson, Pedro y Emilio; instrucciones para sus agentes en docs/sdd/guias-integrantes/. Cuando el grupo decida iniciar: usar `develop` con PR #9/002 ya integrado (02cb26c); crear la rama `feature/*` especificada en cada guía desde `develop`; abrir cada PR hacia `develop` con pruebas y evidencia de aceptación. 003, 004, 006 y 007 pueden iniciar desde la base 002. 005 puede desarrollar y abrir PR con contratos mientras faltan 003/004; 008 hace lo mismo para 003/006. La migración y validación integral requieren proveedores reales: declarar pendientes y ordenar merges sin bloquear el avance individual. Revisar conflictos de migraciones al integrar cambios paralelos.

Antes de implementar, ratificar la Constitución con el grupo, completar la facultad verificada de todos los activos legados antes de aplicar la restricción, y fijar límites operativos CSV como tarea técnica T002 de 008. PR #9 ya está integrado en develop; esta preparación parte de 02cb26c.
