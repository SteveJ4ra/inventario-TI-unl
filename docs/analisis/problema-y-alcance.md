# Análisis y delimitación del problema

- **Proyecto:** Inventario de Tecnologías de Información (Proyecto N.º 2)
- **Universidad:** Universidad Nacional de Loja — Carrera de Computación
- **Asignatura:** Desarrollo Basado en Plataformas · ACD1 / AA1 / APE1
- **Grupo:** N.º 5 (seis integrantes)
- **Responsable:** Yandri — Rol 1: análisis del problema, contexto, alcance y límites
- **Versión:** 0.2 · 10/10/2026 · Revisión actualizada para consideración del equipo
**Estado:** Aporte individual revisado; pendiente de aprobación formal del contenido y de su integración en GitHub.

**Criterio de certeza:** **Confirmado** = enunciado del proyecto o acuerdo expreso comunicado por el equipo; **Propuesta** = delimitación formulada para el proyecto académico; **Pendiente** = información que requiere validación del docente, la DTI o los responsables del proceso. La selección tecnológica grupal no equivale a la aprobación institucional de los requisitos.

## 1. Contexto y situación actual

### 1.1. Contexto del problema

El proyecto procede del banco de problemas de la asignatura, con origen en el portafolio remitido por la Dirección de Tecnologías de la Información (DTI). Su necesidad central es administrar información de activos tecnológicos, ubicación, responsable o custodio, estado y movimientos para conocer su situación actual y parte de su historial [1].

La unidad principal de análisis es **cada activo individual**, incluso cuando varios equipos comparten marca y modelo. El reto es distinguir la ficha vigente del activo de los acontecimientos de su ciclo de vida, tales como asignación, traslado, mantenimiento, novedad o baja. Las dependencias que participarán y la cobertura organizacional definitiva permanecen pendientes de validación.

### 1.2. Situación actual y evidencia disponible

No se dispone aún de entrevistas, procedimientos oficiales, registros ni observación directa que acrediten cómo administra actualmente la DTI el inventario. Por ello, no se afirma que utilice Excel, registros manuales o determinado sistema, ni se atribuyen errores o pérdidas a la universidad. Sí está respaldada por el enunciado la necesidad de identificar y seguir los activos [1].

La descripción del proceso actual (AS-IS) requerirá aclarar mecanismos de identificación, formatos utilizados, responsables de registro y autorización, cobertura, excepciones y evidencia asociada a cada movimiento. Las herramientas Snipe-IT y GLPI se consultaron únicamente como referentes externos de identificación e historial, no como evidencia del funcionamiento de la DTI [3], [4].

## 2. Formulación del problema

### 2.1. Problema central

Para gestionar los activos tecnológicos en el ámbito considerado por el encargo, se requiere información organizada y trazable que permita identificar cada equipo, conocer su ubicación, custodio y estado actual, y consultar los acontecimientos relevantes de su ciclo de vida. El desafío consiste en **mantener coherencia entre la situación vigente de cada activo y los movimientos que explican sus cambios**, sin confundir el activo con el historial de eventos [1].

### 2.2. Factores y efectos potenciales

Sin asumir fallas institucionales comprobadas, se plantean como factores de riesgo: identificadores no uniformes, movimientos que no conserven trazabilidad, responsabilidades de autorización poco claras y posibles discrepancias entre la situación actual y el historial. Si estuvieran presentes, podrían generar dudas sobre qué equipo fue trasladado, quién lo custodia o en qué momento cambió su condición. Estas hipótesis deben contrastarse con el proceso real.

### 2.3. Justificación

Abordar la necesidad permite establecer requisitos verificables, acordar responsabilidades y definir un primer incremento académico realizable. El beneficio esperado es disponer de una base para consultar tanto el estado actual de los activos como sus cambios históricos, sin presuponer que el sistema se desplegará obligatoriamente en producción.

## 3. Actores y necesidades preliminares

A partir del análisis del equipo y el aporte de Emilio [7], se consideran **tres perfiles candidatos para la solución**, sujetos a validación de atribuciones y permisos:

| Actor propuesto | Necesidad principal | Interacción prevista | Condición pendiente |
|---|---|---|---|
| Gestor de activos | Identificación confiable, situación e historial | Registrar fichas y movimientos; consultar inventario | Determinar quién registra, corrige y autoriza |
| Custodio | Conocer los activos asignados y reportar novedades | Consultar asignaciones, confirmar o informar incidencias | Definir si tendrá cuenta, qué consulta y qué confirma |
| Administrador | Control de accesos y supervisión | Gestionar cuentas, roles y catálogos; consultar reportes | Confirmar límites y responsabilidades reales |

La **DTI** se considera unidad de referencia y posible interesada institucional, no un cuarto perfil técnico confirmado. Encargados de laboratorios, docentes u otros usuarios pueden ser participantes del proceso, pero todavía no se ha determinado si tendrán acceso directo al sistema o interactuarán a través de los tres perfiles anteriores. Ningún permiso se presenta como aprobado por la DTI.

## 4. Alcance y límites del proyecto

### 4.1. Primer incremento académico propuesto

Se propone priorizar activos tecnológicos **físicos** y las operaciones indispensables para garantizar identificación individual y trazabilidad:

- Registrar y consultar cada activo de forma diferenciada, incluso si comparte modelo con otro.
- Consultar ubicación, custodio y estado actual.
- Registrar asignaciones, traslados, novedades, entradas/salidas de mantenimiento y bajas con información histórica básica.
- Conservar la relación entre cambios vigentes y eventos, y aplicar controles de acceso básicos cuando los permisos sean definidos.
- Demostrar el comportamiento utilizando datos ficticios o debidamente autorizados, sin requerir despliegue institucional.

La cobertura de dependencias, categorías definitivas, procedimientos de aprobación y campos obligatorios siguen por aclarar.

### 4.2. Funcionalidades no comprometidas en el primer incremento

No se propone implementar inicialmente un sistema integral de licencias y activos digitales, control de ocupación de laboratorios, gestión completa de reparaciones y costos, descubrimiento automático por red ni integración obligatoria con sistemas institucionales. Se podrán evaluar para etapas posteriores la carga masiva sin perder identificadores individuales y el uso de códigos QR.

**Distinción entre tecnología y alcance:** el equipo acordó **React + TypeScript para la interfaz web** y **React Native + Expo + TypeScript para una aplicación móvil futura** [6], [8]. Esta selección **no implica que la aplicación móvil ni la lectura QR deban entregarse en el primer incremento**. El orden de implementación deberá precisarse en las especificaciones y la planificación del proyecto.

### 4.3. Justificación de las exclusiones

El encargo enfatiza el ciclo de vida del activo. Incluir control de aulas, reparación exhaustiva o integraciones externas desde el inicio ampliaría actores, reglas y esfuerzo sin haberlos validado. La priorización permite concentrar el primer incremento en la trazabilidad y reservar las funciones adicionales para decisiones posteriores.

## 5. Supuestos, restricciones y decisión técnica

### 5.1. Supuestos sujetos a validación

| Supuesto | Validación prevista |
|---|---|
| El primer incremento puede centrarse en bienes físicos de TI | Acordar categorías y cobertura con docente/DTI |
| Existen ubicaciones y responsables diferenciados | Consultar procedimiento y responsables reales |
| Habrá permisos distintos para informar, registrar y aprobar | Definir matriz con Emilio y Anderson |
| Se pueden emplear datos de demostración no sensibles | Acordar fuentes y autorizaciones de prueba |
| QR y carga masiva pueden posponerse | Confirmar prioridades y esfuerzo de la primera entrega |

### 5.2. Restricciones y acuerdos conocidos

| Condición | Fuente o estado | Efecto en el proyecto |
|---|---|---|
| Identificación individual y registro histórico de movimientos | Enunciado del problema [1] | Priorizar consistencia de activos y eventos |
| Proyecto académico de seis integrantes | Información del equipo | Coordinar responsabilidades, documentos y evidencia de contribución |
| Uso de desarrollo guiado por especificaciones (SDD) | Actividades ACD1 / APE1 / AA1 y acuerdo del equipo [2], [5] | Clarificar requisitos antes de implementar |
| Stack tecnológico acordado: **Python + Django + Django REST Framework; React + TypeScript; React Native + Expo + TypeScript; PostgreSQL** | Decisión grupal comunicada el 10/10/2026; propuesta analizada por Alex [6], [8] | Orientar el plan de implementación, no alterar la formulación del problema |

**Trazabilidad de la decisión:** en la versión 0.1 de este informe constaba Java como decisión inicial informada. El equipo eligió posteriormente el stack de Python descrito arriba. No se dispone aquí de acta formal ni de una fecha de reunión que permita atribuir esa ratificación a la DTI o al docente. Tampoco se han confirmado infraestructura, presupuesto, calendario de despliegue ni acceso a datos reales.

## 6. Riesgos iniciales

La probabilidad y el impacto se expresan de manera **cualitativa** (A = alta; M = media; B = baja), como estimaciones del equipo, no como mediciones institucionales.

| Riesgo | Prob. | Impacto | Acción preventiva |
|---|---|---|---|
| Alcance o categorías sin validar; desarrollo de funciones no pertinentes | A | A | Acordar incremento mínimo y documentar preguntas |
| Roles y autorizaciones indefinidos | M | A | Revisar mapa de actores y matriz de permisos |
| Cambio de estado sin evento que explique el movimiento | M | A | Definir reglas de consistencia e historial y pruebas |
| Crecimiento excesivo del alcance | A | M | Mantener exclusiones y priorizar el reto central |
| Falta de datos institucionales autorizados para probar | M | M | Utilizar datos sintéticos y escenarios revisables |
| Integración de componentes con criterios funcionales distintos | M | M | Mantener especificaciones compartidas y revisar integración temprana |

Se mantiene como riesgo prioritario **construir sobre un alcance o reglas no validados**, por su efecto transversal sobre actores, pruebas y futura implementación.

## 7. Criterios preliminares de éxito

Estos criterios se proponen para comprobar el **prototipo académico** cuando exista; todavía no representan resultados obtenidos ni metas institucionales aprobadas.

| Resultado esperado | Criterio de aceptación propuesto | Evidencia futura |
|---|---|---|
| Identificación individual | No se aceptan dos activos con el mismo identificador de inventario | Registrar equipos similares e intentar duplicar un código |
| Situación actual coherente | Ubicación, custodio y estado reflejan el último movimiento válido | Consultar antes y después de traslado o reasignación |
| Historial verificable | Cada movimiento conserva activo, tipo, fecha y responsable registrador | Ejecutar secuencia de movimientos de prueba |
| Consistencia de movimientos | Un cambio inválido no altera la situación oficial sin la regla correspondiente | Probar movimientos válidos, rechazados y correcciones |
| Permisos básicos | Un perfil no autorizado no modifica registros oficiales | Pruebas con permisos acordados |
| Baja trazable | Un activo dado de baja conserva su identidad e historial | Dar de baja un activo ficticio y consultar antecedentes |

**Objetivo preliminar:** favorecer una gestión identificable, actualizada y trazable de los activos tecnológicos para que personas autorizadas conozcan tanto su situación vigente como los acontecimientos relevantes de su ciclo de vida.

## 8. Preguntas de clarificación

Las siguientes preguntas deben trasladarse al proceso `clarify` coordinado por Pedro y Anderson. Son cuestiones pendientes y **no constituyen respuestas ya aprobadas**.

**P01. Cobertura:** ¿El sistema atenderá a toda la universidad, solo a la DTI o a dependencias determinadas? ¿Qué escenario de prueba se utilizará?

**P02. Proceso actual:** ¿Cómo se identifican, registran y autorizan actualmente las altas, asignaciones, traslados, mantenimientos y bajas?

**P03. Categorías:** ¿Qué tipos de activos y datos obligatorios se incluirán en el primer incremento? ¿Los identificadores de inventario se asignan con reglas institucionales existentes?

**P04. Actores y permisos:** ¿Quién consulta, registra, aprueba o corrige movimientos? ¿El custodio tendrá cuenta propia o confirmará por otro procedimiento?

**P05. Historial y correcciones:** ¿Qué datos deberá conservar cada movimiento y cómo se subsanará un error sin perder evidencia histórica?

**P06. Etapas web y móvil:** ¿Qué operaciones mínimas se esperan en web y cuáles se reservan para la app móvil posterior? ¿Se requiere QR y qué información podría exponerse de forma segura?

## 9. Revisión, coordinación y evidencia de contribución

### 9.1. Control de versiones

- **Versión 0.1 (09/10/2026):** propuesta individual original; incluía Java como selección inicial informada.
- **Versión 0.2 (10/10/2026):** se actualiza el acuerdo tecnológico, se armonizan los actores con Emilio y se distingue el primer incremento del alcance móvil futuro. **Estado: revisión individual para consideración del grupo**, sin declaración de aprobación formal del contenido.

### 9.2. Registro de retroalimentación y ajustes

| Información recibida | Modificación efectuada | Evidencia disponible |
|---|---|---|
| El equipo decidió trabajar con Python y el stack propuesto por Alex | Se actualizaron la sección 5.2, la coordinación y D08 | Comunicación de coordinación del grupo [8]; acta formal no disponible |
| Emilio documentó gestor, custodio y administrador como tres perfiles de referencia | Se armonizó la descripción de actores, manteniendo permisos pendientes | Documento de Emilio [7] |
| La aplicación móvil se prevé para etapas posteriores | Se diferenciaron la selección React Native y el alcance del primer incremento | Documentos de Alex y Emilio [6], [7] |

### 9.3. Coordinación y entrega a otros roles

| Integrante | Contenido para compartir |
|---|---|
| Emilio | Actores candidatos, información por aclarar y diferencia entre custodio y usuario |
| Pedro y Anderson | Preguntas P01–P06, supuestos, alcance y criterios verificables para SDD |
| Alex | Problema central, necesidades, riesgos y stack aprobado por el equipo: Python/Django/DRF, React/TypeScript, React Native/Expo y PostgreSQL |
| Steven / equipo | Alcance propuesto, exclusiones, riesgos, decisiones informadas y cuestiones pendientes para control de versiones |

La evidencia de contribución individual en GitHub (rama propia, commits, Pull Request, revisión y merge) se agregará **solo cuando esas acciones se ejecuten y puedan verificarse**. El documento original y la revisión son aportes académicos; no se afirma que ya estén publicados en el repositorio.

## 10. Fuentes, integridad y comprobación

### 10.1. Referencias

[1] Universidad Nacional de Loja, *Banco de proyectos para análisis en ACD1*, proyecto N.º 2: «Inventario de Tecnologías de Información», 2026. Documento proporcionado por la asignatura.

[2] *Plantilla Rol 1: Análisis y delimitación del problema*, material de estructura académica facilitado al estudiante, 2026.

[3] Snipe-IT, *Overview* y *Asset Tags*, documentación oficial: https://snipe-it.readme.io/docs/overview y https://snipe-it.readme.io/docs/asset-tags (consultado en el informe original el 09/10/2026).

[4] GLPI Project, *Computers — History*, documentación oficial: https://help.glpi-project.org/documentation/modules/assets/computers (consultado en el informe original el 09/10/2026).

[5] GitHub, *Spec Kit: Spec-Driven Development*, repositorio oficial: https://github.com/github/spec-kit (referencia de SDD y flujo de especificaciones).

[6] Alex, *Análisis tecnológico y alternativas* (ACD1) y *Análisis tecnológico y decisión inicial del stack* (APE1), aportes del equipo, 2026.

[7] Emilio, *Identificación y clasificación de actores*, aporte del equipo, 2026.

[8] Acuerdos tecnológicos del Grupo N.º 5 comunicados por Steven durante la revisión colaborativa del 10/10/2026. Sin acta formal incorporada a este documento.

### 10.2. Declaración de utilización de inteligencia artificial

Se utilizó ChatGPT (OpenAI) como apoyo para estructurar el análisis original, identificar inconsistencias entre versiones, contrastar aportes del equipo, proponer ajustes de redacción y revisar criterios de éxito, riesgos y clarificaciones. El responsable del aporte debe revisar y aprobar la formulación final antes de entregarla. No se presentan como verificadas las hipótesis sobre el funcionamiento de la DTI ni como ejecutadas las comprobaciones del prototipo.

### 10.3. Lista final de comprobación antes de publicar

- [ ] El problema está formulado sin confundir necesidad institucional con tecnología elegida.
- [ ] Los actores están armonizados con Emilio y sus permisos no se dan por aprobados.
- [ ] Primer incremento y aplicaciones futuras están claramente diferenciados.
- [ ] La sección 5.2 y D08 reflejan el stack acordado, sin referencias vigentes a Java.
- [ ] Riesgos y criterios de éxito se presentan como propuestas verificables, no resultados medidos.
- [ ] Las preguntas de clarificación permanecen abiertas donde corresponde.
- [ ] Fechas, participantes y revisiones solo se registran cuando existe evidencia.
- [ ] Fuentes y declaración de IA representan el trabajo realmente realizado.
- [ ] El archivo de trabajo está revisado antes de producir la versión Git/Markdown y realizar el Pull Request.

## Anexo A. Registro de decisiones

| ID | Decisión o propuesta | Estado a 10/10/2026 |
|---|---|---|
| D01 | Priorizar activos de TI físicos en el primer incremento | Propuesta; validar cobertura y categorías |
| D02 | Identificar cada unidad separadamente; evaluar carga masiva | Identificación individual respaldada por el reto; carga masiva condicionada |
| D03 | Excluir control de ocupación de laboratorios en tiempo real | Propuesta de delimitación |
| D04 | Registrar mantenimiento básico, sin gestión integral de reparación | Propuesta de delimitación |
| D05 | Permitir reportar novedades sin autorización automática para modificar la ficha | Propuesta; permisos por confirmar |
| D06 | Diseñar para distintas ubicaciones y demostrar con datos representativos | Propuesta; cobertura institucional por confirmar |
| D07 | No prometer despliegue obligatorio en la UNL | Aclaración comunicada por el equipo; dependerá de evaluación posterior |
| D08 | Adoptar **Python + Django + DRF; React + TypeScript; React Native + Expo + TypeScript; PostgreSQL**, y trabajar mediante SDD | **Acuerdo tecnológico del equipo comunicado el 10/10/2026**; sustituye Java consignado en la versión 0.1. No implica aprobación de requisitos por DTI |

## Anexo B. Validación del aporte por el equipo

**Estado actual:** pendiente de revisión formal del documento 0.2 y registro de la contribución en GitHub.

**Registro pendiente:** fecha, participantes, observaciones, decisiones validadas, enlace al commit/PR y resultado de la revisión. Ningún requisito se atribuye como aprobado por la DTI.
