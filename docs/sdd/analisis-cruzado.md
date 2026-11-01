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

- Usar develop actualizado con PR #9/002 integrado (02cb26c).
- Revisar y ratificar Constitución y alcance con el equipo.
- Preparar el mapeo verificado de facultades para todos los activos existentes antes de aplicar migraciones de 003.
- Definir límites técnicos de bytes, filas y expiración del preview CSV en T002 de 008 antes de habilitar la importación.
- No quedan decisiones funcionales abiertas en el alcance aclarado por el responsable; antes de implementar, el equipo debe ratificar estas reglas junto con el resto del alcance.
- En implementación, revisar dependencias y conflictos de migraciones; la integración/validación integral de 005 requiere 003+004 y la de 008 requiere 003+006. El desarrollo aislado y apertura del PR pueden avanzar en paralelo siguiendo las guías individuales.

## Validación pendiente

No se ejecutaron pruebas de backend/frontend ni se revisó código nuevo. Cada `validation-plan.md` define la evidencia que debe producirse después de implementar. Solo se verificó consistencia documental y `git diff --check`.

## Segunda revisión previa al PR

La primera revisión de cobertura no detectó varios conflictos con la implementación 002. Esta segunda revisión contrastó models.py, services.py, permissions.py, auth_views.py, urls.py, dependencias y selector de contexto Spec Kit. Se corrigieron:

| Hallazgo | Corrección y cobertura |
|---|---|
| Operador requerido en 003, creado solo en 005 | Provisión, sesión y permisos mínimos pasan a fundamentos de 003; 005 los reutiliza. T002/T007 de 003 y T004/T005 de 005. |
| Sesión actual usa 403, varios contratos exigían 401 | Contratos alineados al HTTP 403 de 002. |
| Limpiar custodia de Asignado violaba asset_custody_consistent | En No localizado/Baja asignación y custodio actuales son null; 004 reemplaza constraint, preserva snapshots y actualiza guardas. T002/T004 de 004. |
| Rectificación de 002 ignoraba eventos de tablas nuevas | Revisión global y elegibilidad por resulting_revision; bajas enlazadas a Movement para reutilizar movement_id/rectifies. T006/T017 de 003, T004 de 004 y T002/T008 de 005. |
| Alta de factura requería activos y alta de activo requería factura | Documento de metadatos primero; alta atómica activo+línea después. T006/T008 de 003. |
| Cierre de mantenimiento entregaba ubicación previa demasiado tarde | GET de detalle devuelve ubicación previa antes del POST de cierre. T005/T009 de 004. |
| QR no tenía resolución de código TI a ficha | Ruta autenticada exacta by-code, sin búsqueda parcial. T004/T007 de 007. |
| Importación aplicada devolvía 409 y también prometía idempotencia | 201 primera aplicación, 200 reintento; batch bloqueado y revalidación completa. T007/T013 de 008. |
| Preview guardaba resumen pero no garantizaba datos para aplicar | Filas normalizadas inmutables, hash, propietario y resultado mínimo. T005/T007 de 008. |
| Modelo de licencias discrepaba de FR-003 y nombres de revisión | Modelo alineado a enteros no negativos; vendor/revision canónicos y fecha fin inclusiva. T004/T010 de 006. |
| Referencia sola podía fusionar facturas distintas en CSV | document_key local o id existente explícito; coherencia de metadatos por grupo. T003/T012 de 008. |
| Selector Spec Kit seguía fijado en 002 | Instrucciones de selección explícita sin persistencia en README y quickstarts; chequeo de los seis directorios. |
| Documentos seguían declarando PR #9 pendiente | Actualizados a merge confirmado 02cb26c. |

Los detalles comunes están en [contratos transversales](contratos-transversales.md). Los planes de validación incorporan regresiones específicas para estas correcciones. Quedan revisión/ratificación grupal, preparación de datos legados y valores operativos CSV como gates explícitos; no son funcionalidades adicionales ni evidencia de tests aprobados.

### Comprobaciones finales

Se ejecutó check-prerequisites.ps1 con RequireSpec/RequireTasks/IncludeTasks y selección explícita, sin persistencia, para 003, 004, 005, 006, 007 y 008: los seis devolvieron su FEATURE_DIR correcto y documentos requeridos. Se comprobó presencia de artefactos, IDs FR/SC/T sin duplicados, cobertura FR→tarea (expandiendo rangos), enlaces locales y whitespace del diff. No se ejecutaron pruebas de código porque el cambio es exclusivamente documental; los escenarios de regresión agregados son trabajo futuro.
