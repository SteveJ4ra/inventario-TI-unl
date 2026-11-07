# Documentación SDD — Inventario TI

## Fuente de verdad

- [Alcance backend y dependencias](alcance-backend-completo.md): alcance, exclusiones, etapas SDD y gates de implementación.
- [Registro de decisiones](decisiones-alcance-backend.md): respuestas confirmadas del responsable, DBE-001 a DBE-051. Pendiente revisión del equipo.
- [Análisis cruzado](analisis-cruzado.md): cobertura entre requisitos, planes y tareas, hallazgos corregidos y gates restantes.
- [Constitución propuesta](../../.specify/memory/constitution.md): principios del grupo, pendiente de ratificación; no representa política institucional.

## Incrementos backend

| Incremento | Paquete | Estado SDD | Dependencia principal |
|---|---|---|---|
| 002 | [Registro y consulta](../../specs/002-registro-consulta-activos/) | Base implementada; PR #9 integrado en develop (02cb26c) | Base actual |
| 003 | [Fichas y adquisiciones](../../specs/003-fichas-adquisiciones/) | Artefactos SDD preparados | 002 |
| 004 | [Novedades y mantenimiento](../../specs/004-novedades-mantenimiento/) | Artefactos SDD preparados | 002 |
| 005 | [Bajas y aprobación](../../specs/005-bajas-aprobacion/) | Artefactos SDD preparados | 003 y 004 |
| 006 | [Lotes de licencias](../../specs/006-lotes-licencias/) | Artefactos SDD preparados | 002 |
| 007 | [QR de activos](../../specs/007-qr-activos/) | Artefactos SDD preparados | 002 |
| 008 | [Importación CSV](../../specs/008-importacion-csv/) | Artefactos SDD preparados | 003 y 006 |

Los paquetes 003–008 permanecen completos y se asignaron según las [guías individuales](guias-integrantes/README.md), orientadas a los agentes de código de cada integrante. Las carpetas `docs/sdd/borradores-anderson/` contienen material previo de preparación/demostración y no prevalecen sobre estos artefactos activos ni sobre las decisiones del equipo.

## Contrato de integración

Consultar [contratos técnicos transversales](contratos-transversales.md) antes de implementar: detalla acceso, revisión global, invariantes de custodia, historial, importación y compatibilidad con 002.

## Seleccionar el paquete correcto en Spec Kit

La configuración compartida `.specify/feature.json` sigue apuntando a 002; no basta cambiar de rama. En la raíz del repositorio, indicar el paquete antes de Analyze/Implement y comprobar que FEATURE_DIR corresponde al elegido. Ejemplo PowerShell (sustituir 003 por la carpeta real):

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-fichas-adquisiciones'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

Mantener estas variables en la sesión que ejecutará el flujo. Al cambiar de paquete actualizar SPECIFY_FEATURE_DIRECTORY. NO_PERSIST evita sobrescribir la selección compartida de otro integrante. Ningún comando de implementación debe empezar si FEATURE_DIR no coincide con la feature que se va a trabajar.
