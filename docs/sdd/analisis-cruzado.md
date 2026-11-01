# Análisis cruzado SDD — Backend Inventario TI

**Fecha:** 1 de noviembre de 2026
**Alcance revisado:** paquetes 003–008 y Constitución propuesta.
**Tipo:** revisión documental de coherencia; no es validación de código ni ratificación institucional.

## Resultado

Los artefactos están listos para revisión del grupo y, después de resolver los gates indicados, para iniciar implementación por feature. Las especificaciones no declaran funcionalidades implementadas.

| Paquete | FR | Criterios de éxito | Tareas | Resultado del cruce |
|---|---:|---:|---:|---|
| 003 Fichas/adquisiciones | 16 | 6 | 18 | Cobertura FR→tareas; migración exige asignar facultad verificada a los registros legados. |
| 004 Novedades/mantenimiento | 16 | 5 | 17 | Cobertura FR→tareas; reglas separan localización, condición, asignación y mantenimiento. |
| 005 Bajas/aprobación | 17 | 8 | 19 | Cobertura FR→tareas; depende de facultades de 003 y recuperación de 004. |
| 006 Lotes de licencias | 12 | 5 | 13 | Cobertura FR→tareas; inicio obligatorio, fin opcional y remanente visible aunque vencido. |
| 007 QR | 8 | 5 | 10 | Cobertura FR→tareas; SVG derivado y ficha siempre autenticada. |
| 008 Importación CSV | 12 | 6 | 14 | Cobertura FR→tareas; validación completa, mismo Gestor confirma, todo-o-nada. |
| **Total** | **81** | **35** | **91** | Todas las tareas permanecen pendientes. |

## Hallazgos tratados

1. 007 no tenía criterios de éxito ni trazabilidad completa; se agregaron IDs FR/SC y mapa requisito-tarea.
2. 008 carecía de IDs FR/SC; se añadieron y se enlazaron con tareas verificables.
3. La migración de activos 002 no podía inventar facultades; DBE-048 define completarlas manualmente con datos verificados antes de aplicar la restricción.
4. La facultad responsable influye en aprobaciones y podía editarse por la ruta general; DBE-050 establece ruta exclusiva de Operador, auditoría y bloqueo si hay solicitud pendiente.
7. DBE-051 define al Operador como único actor que reasigna solicitudes pendientes de revisión.
5. Se incorporó la provisión local de la cuenta inicial de Operador (DBE-047) y el mismo Gestor para las dos confirmaciones CSV (DBE-049).
6. Se aclaró que la fecha inicial de licencia es obligatoria (DBE-044).

## Constitución y seguridad

No se identificó contradicción con los principios propuestos de trazabilidad, integridad, seguridad, calidad verificable y simplicidad. La Constitución sigue pendiente de ratificación por los seis integrantes; las decisiones funcionales tampoco se presentan como políticas institucionales de la UNL.

Se conservan controles de autenticación por Gestor, operador limitado a administración definida, revisor limitado a solicitudes asignadas, auditoría de cambios sensibles y ausencia de claves/documentos binarios. La revisión de implementación debe verificar autorización por endpoint y que el QR no funcione como credencial. El operador es el único que puede modificar facultades y reasignar solicitudes, con las restricciones correspondientes.

## Gates antes de implementar

- Integrar PR #9/002 en `develop`; no basar nuevas features en un `develop` que aún no contenga el modelo inicial.
- Revisar y ratificar Constitución y alcance con el equipo.
- Preparar el mapeo verificado de facultades para todos los activos existentes antes de aplicar migraciones de 003.
- Definir límites técnicos de bytes, filas y expiración del preview CSV en T002 de 008 antes de habilitar la importación.
- No quedan decisiones funcionales abiertas en el alcance aclarado por el responsable; antes de implementar, el equipo debe ratificar estas reglas junto con el resto del alcance.
- En implementación, revisar dependencias y conflictos de migraciones; 005 espera a 003+004 y 008 a 003+006.

## Validación pendiente

No se ejecutaron pruebas de backend/frontend ni se revisó código nuevo. Cada `validation-plan.md` define la evidencia que debe producirse después de implementar. Solo se verificó consistencia documental y `git diff --check`.
