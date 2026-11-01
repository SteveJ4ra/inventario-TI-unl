# Documentación SDD — Inventario TI

## Fuente de verdad

- [Alcance backend y dependencias](alcance-backend-completo.md): alcance, exclusiones, etapas SDD y gates de implementación.
- [Registro de decisiones](decisiones-alcance-backend.md): respuestas confirmadas del responsable, DBE-001 a DBE-051. Pendiente revisión del equipo.
- [Análisis cruzado](analisis-cruzado.md): cobertura entre requisitos, planes y tareas, hallazgos corregidos y gates restantes.
- [Constitución propuesta](../../.specify/memory/constitution.md): principios del grupo, pendiente de ratificación; no representa política institucional.

## Incrementos backend

| Incremento | Paquete | Estado SDD | Dependencia principal |
|---|---|---|---|
| 002 | [Registro y consulta](../../specs/002-registro-consulta-activos/) | Base implementada; PR #9 pendiente de integración | Base actual |
| 003 | [Fichas y adquisiciones](../../specs/003-fichas-adquisiciones/) | Artefactos SDD preparados | 002 |
| 004 | [Novedades y mantenimiento](../../specs/004-novedades-mantenimiento/) | Artefactos SDD preparados | 002 |
| 005 | [Bajas y aprobación](../../specs/005-bajas-aprobacion/) | Artefactos SDD preparados | 003 y 004 |
| 006 | [Lotes de licencias](../../specs/006-lotes-licencias/) | Artefactos SDD preparados | 002 |
| 007 | [QR de activos](../../specs/007-qr-activos/) | Artefactos SDD preparados | 002 |
| 008 | [Importación CSV](../../specs/008-importacion-csv/) | Artefactos SDD preparados | 003 y 006 |

Los paquetes 003–008 permanecen completos; no se dividieron ni asignaron a integrantes. Las carpetas `docs/sdd/borradores-anderson/` contienen material previo de preparación/demostración y no prevalecen sobre estos artefactos activos ni sobre las decisiones del equipo.
