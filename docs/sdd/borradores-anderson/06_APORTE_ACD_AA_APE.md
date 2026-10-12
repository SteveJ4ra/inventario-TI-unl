# Aportes de Anderson para integrar a las tres entregas

**No es la entrega grupal completa.** Debe incorporarse, revisarse y adaptarse a los documentos que arme el equipo. No incluye actores aprobados, stack definitivo ni retroalimentación del ingeniero.

## ACD 1 — Relación inicial del problema con SDD (aporte de Anderson)

El desarrollo guiado por especificaciones permite estructurar el trabajo antes de implementar. En el caso de **Inventario de TI**, la ficha del banco académico establece como necesidad gestionar información del activo, su ubicación, responsable/custodio, estado y movimientos. En una aplicación inicial de SDD, `constitution` permitiría acordar principios de calidad y colaboración; `specify` describiría comportamientos verificables dentro de un alcance aprobado; `clarify` identificaría dudas sobre identificadores, permisos e historial; `plan` traduciría requisitos validados en decisiones técnicas; y `tasks` descompondría ese plan en acciones concretas. El grupo aún debe confirmar el alcance y las reglas específicas antes de presentar estos artefactos como definitivos.

**Pendiente ACD:** registrar retroalimentación real recibida del docente y decisiones revisadas. No inventarla. Los elementos de problema/actores/stack pertenecen a las secciones de Yandri, Emilio y Alex.

## AA 1 — Explicación sintetizada de SDD y Spec Kit (aporte de Anderson)

**SDD** es un enfoque en el que las especificaciones claras, verificables y evolutivas orientan las decisiones técnicas y la implementación. El **problema** describe la necesidad; un **requisito** plantea un comportamiento o condición necesaria; la **especificación** los organiza en un documento suficientemente preciso y comprobable; y la **solución técnica** explica cómo se construirá el comportamiento acordado. Por eso una especificación debe preceder a la implementación: reduce interpretaciones contradictorias y permite asociar requisitos, decisiones y pruebas. La **clarificación** consiste en resolver ambigüedades antes de basar un plan en suposiciones.

**Spec Kit** es una herramienta concreta que apoya ese enfoque: `constitution` define principios del proyecto; `specify` transforma la necesidad en requisitos/historias; `clarify` ayuda a despejar dudas; `plan` decide el diseño y las tecnologías; `tasks` crea trabajo ejecutable a partir del plan. No son sinónimos: **SDD es la metodología; Spec Kit es una implementación posible**.

**Ejemplo:** conocer el custodio actual de un activo es una intención; consultar el dato autorizado podría convertirse en requisito tras validación; elegir clases, tablas y endpoints corresponde al plan. El banco **no define aún** permisos o estructura de la base de datos.

**Pendiente AA:** la tabla y el mapa de actores los prepara Emilio; las cinco o más preguntas las coordina Pedro; toda respuesta requiere fuente. Registrar declaración de IA y bibliografía consolidada.

## APE 1 — Evidencia técnica y contribución de Anderson

**Entorno observado en la conversación:** Ubuntu Linux, Python 3.14.4, Git 2.53.0, uv 0.11.26, `specify-cli` 1.1.2 y OpenCode 1.18.35 (captura facilitada por Anderson). Se observó la inicialización de `inventario-ti-practica`, comandos en `.opencode/commands/` y una ejecución de `/speckit.constitution` que generó `.specify/memory/constitution.md`.

**Limitación importante:** la constitución inicial fue generada por el agente desde el nombre del proyecto, sin recibir decisiones reales del equipo; asignó principios no ratificados, TDD obligatorio y una versión declarada como ratificada. Debe revisarse, conservar evidencia del cambio y corregirse antes de integrarla.

**Redacción sugerida de contribución personal (edita para que sea VERDADERA al entregar):**

> Como responsable de la aplicación inicial de SDD, preparé un entorno de práctica con GitHub Spec Kit y OpenCode, identifiqué los artefactos del flujo `constitution`, `specify`, `clarify`, `plan` y `tasks`, y revisé críticamente la constitución generada para separar principios propuestos de decisiones confirmadas. Registré los puntos pendientes y coordiné la preparación del material que será integrado al repositorio común. *(Actualizar según pasos realmente completados; no atribuirse acciones aún no hechas.)*

### Evidencias que Anderson debe generar de verdad

- Captura propia o salida de `specify version`.
- Captura de `.opencode/commands/` y `.specify/`.
- Antes/después de la revisión real de `constitution.md`.
- Evidencia de una especificación preliminar generada o revisada dentro de OpenCode (si se ejecuta).
- Commits o PR propios en la rama asignada por Steven **una vez establecido el repositorio grupal**.
- Explicación de lo que falta por confirmar y por qué no se ha implementado un backend completo.

## Fuentes para citar en el informe del equipo

- Banco de Proyectos para ACD1 (2026), ficha 2, p. 3.
- Guía APE 001 (2026), secciones 3, 6, 7, 8 y 9, pp. 1–5.
- Guía detallada SDD (2026), secciones 1, 2, 5, 7, 10, 21, 23, pp. 3–17.
- GitHub, *Spec Kit*, https://github.github.io/spec-kit/quickstart.html .

**Declaración de IA sugerida:** «Se utilizó ChatGPT como herramienta de apoyo para organizar y revisar borradores de documentación SDD y OpenCode para generar/revisar artefactos de práctica. Las decisiones fueron sometidas a revisión humana; no se consideran confirmadas las reglas que no constan en las fuentes o acuerdos del proyecto». Adaptar a los usos efectivos de cada integrante.
