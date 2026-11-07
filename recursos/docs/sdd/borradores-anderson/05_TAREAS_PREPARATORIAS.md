# Tareas preparatorias de Anderson (NO `tasks.md` técnico definitivo)

Esta lista corresponde al trabajo **de primera semana para organizar SDD**. No afirmar que es la salida de `/speckit.tasks` hasta ejecutar el comando después de tener un `plan.md` revisado.

| ID | Tarea concreta | Evidencia verificable | Dependencia |
|---|---|---|---|
| SDD-01 | Revisar ficha del inventario y guía SDD | Registro de fuentes y alcance de hechos confirmados | Ninguna |
| SDD-02 | Preparar borrador de constitución y señalar no aprobados | `.specify/memory/constitution.md` revisado o documento borrador | Discusión posterior del equipo |
| SDD-03 | Comprobar la estructura real creada por Spec Kit/OpenCode | Captura o salida `find` / `ls` del proyecto | Instalación existente |
| SDD-04 | Preparar especificación demostrativa sin fijar tecnología | Documento preliminar con estados PROPUESTO/PENDIENTE | Banco oficial |
| SDD-05 | Vincular preguntas de clarificación con decisiones afectadas | Registro Q01...Q12, sin respuestas fabricadas | Coordinación con Pedro |
| SDD-06 | Registrar faltantes del plan y esperar stack | Plan/esqueleto con fuentes de decisión pendientes | Alex y equipo |
| SDD-07 | Explicar el flujo Constitution → Specify → Clarify → Plan → Tasks | Síntesis del proceso en ACD/AA y demostración APE | Trabajo de Anderson |
| SDD-08 | Guardar evidencias de autoría y revisión | Commits, PR o documento identificado; capturas propias | Coordinación con Steven |
| SDD-09 | Participar en revisión grupal y registrar observaciones | Registro de revisión/retroalimentación auténtica | Grupo y docente |

## Ejemplo de descomposición técnica FUTURA (HIPOTÉTICA)

Si se valida la funcionalidad de consulta de un activo, más adelante una herramienta podría derivar tareas como: definir contrato de consulta → definir validaciones → implementar caso de uso → implementar adaptador de persistencia → probar escenario aceptado. **No afirmar que el profesor pidió estas tareas ahora ni que están implementadas**.

## Condición para ejecutar `/speckit.tasks`

Tener una especificación revisada, clarificaciones que afectan el diseño resueltas y un plan coherente, con decisiones tecnológicas del equipo. Entonces ejecutar el comando en OpenCode, revisar el archivo generado y corregir tareas sin fundamento.
