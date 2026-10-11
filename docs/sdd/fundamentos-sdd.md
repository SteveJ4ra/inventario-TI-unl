# Fundamentos de Spec-Driven Development (SDD)

- **Aplicación al proyecto:** Sistema de Inventario de TI
- **Responsable:** Pedro

## 1. ¿Qué es Spec-Driven Development (SDD)?

Spec-Driven Development (SDD), o desarrollo guiado por especificaciones, es un enfoque de desarrollo de software en el que las especificaciones del sistema orientan las decisiones de diseño, planificación e implementación. Su propósito es establecer claramente qué se necesita construir y por qué, antes de decidir cómo implementarlo. Esto ayuda a reducir ambigüedades, mantener la coherencia entre los requisitos y la solución tecnológica, y verificar que el software responda a las necesidades identificadas.

En lugar de comenzar a programar a partir de una idea general, SDD propone documentar los requisitos y convertirlos progresivamente en un plan técnico y tareas concretas. Las especificaciones pueden revisarse y actualizarse a medida que se obtiene nueva información.

## 2. Diferencia entre problema, requisito, especificación y solución técnica

Estos conceptos están relacionados, pero cumplen funciones diferentes dentro de un proyecto de software.

| Concepto | Descripción | Ejemplo general |
|---|---|---|
| **Problema** | Situación o necesidad que se busca resolver. | Dificultad para controlar los activos tecnológicos. |
| **Requisito** | Necesidad o condición que debe cumplir el sistema. | El sistema debe permitir registrar y consultar activos. |
| **Especificación** | Descripción organizada, precisa y verificable del comportamiento esperado. | Un usuario autorizado registra un activo con campos obligatorios y consulta los registros. |
| **Solución técnica** | Tecnologías, arquitectura y mecanismos elegidos para implementar requisitos. | Desarrollar una API backend conectada a una base de datos. |

El problema explica por qué se necesita el sistema; los requisitos establecen qué debe cumplir; la especificación concreta el comportamiento esperado, y la solución técnica determina cómo se construirá. Elegir una tecnología antes de comprender la necesidad puede conducir a una solución inadecuada.

## 3. Importancia de definir las especificaciones antes de implementar

Definir las especificaciones antes de implementar permite:

- Reducir interpretaciones diferentes entre los integrantes del equipo.
- Identificar información faltante, restricciones y casos que necesitan aclaración.
- Establecer criterios para verificar el funcionamiento esperado.
- Organizar el trabajo en tareas comprensibles y asignables.
- Mantener la relación entre las necesidades del proyecto y las funcionalidades implementadas.

Las especificaciones pueden evolucionar conforme el equipo comprende mejor el problema, siempre que los cambios se documenten y se revisen sus consecuencias. SDD no significa solamente escribir documentación antes de programar, sino utilizarla activamente para orientar y comprobar el desarrollo.

## 4. Fundamentos de GitHub Spec Kit

GitHub Spec Kit es una herramienta de código abierto que proporciona estructuras, plantillas y procesos para apoyar el desarrollo guiado por especificaciones. Su flujo ayuda a establecer principios, elaborar especificaciones, definir un plan técnico y generar tareas que orientan la implementación.

### 4.1. Constitution

Establece los principios y reglas generales del proyecto: calidad del código, pruebas, seguridad, mantenibilidad, documentación y convenciones. **Ejemplo:** validar las funcionalidades mediante pruebas y documentar decisiones importantes.

### 4.2. Specify

Describe qué se necesita construir y por qué, centrándose en las necesidades de los usuarios y el comportamiento esperado. Puede incluir requisitos, escenarios de uso y criterios de aceptación. **Ejemplo:** definir que un usuario autorizado pueda registrar, consultar y modificar información de activos.

### 4.3. Clarify

Ayuda a identificar y resolver ambigüedades, contradicciones o información insuficiente. Se formulan preguntas sobre actores, reglas, restricciones y casos especiales. **Ejemplo:** determinar qué ocurre cuando un equipo se devuelve o cuando dos activos tienen el mismo número de serie.

### 4.4. Plan

Convierte la especificación en una propuesta técnica considerando el stack, la arquitectura, las herramientas, las estructuras de datos y las restricciones. **Ejemplo:** seleccionar un lenguaje para el backend y definir su interacción con la base de datos.

### 4.5. Tasks

Descompone el plan en tareas concretas, asignables y verificables. **Ejemplo:** configurar el entorno, implementar el registro de activos y crear pruebas.

### Relación entre las cinco etapas

| Etapa | Pregunta principal | Resultado esperado |
|---|---|---|
| `constitution` | ¿Qué principios debemos respetar? | Principios y reglas del proyecto. |
| `specify` | ¿Qué necesitamos construir y por qué? | Especificación de requisitos y comportamiento. |
| `clarify` | ¿Qué dudas debemos resolver? | Ambigüedades identificadas y decisiones aclaradas. |
| `plan` | ¿Cómo proponemos construirlo? | Plan de implementación técnica. |
| `tasks` | ¿Qué trabajos concretos debemos realizar? | Lista organizada de tareas ejecutables. |

Para esta actividad, el flujo propuesto es establecer principios, elaborar la especificación, aclarar dudas relevantes, preparar el plan técnico y descomponerlo en tareas. La clarificación ayuda a mejorar la calidad del proceso; no todos los flujos básicos la exigen como paso obligatorio, aunque esta actividad académica la incluye expresamente.

## 5. Preguntas de clarificación aplicables al Inventario de TI

Antes de diseñar e implementar la solución, el equipo debe formular preguntas que permitan comprender mejor el problema y evitar asumir requisitos no confirmados. Las siguientes son propuestas iniciales que deben revisarse con el equipo.

1. **¿Qué tipos de activos tecnológicos se administrarán?** Determinar si incluirá computadoras, laptops, monitores, impresoras, servidores, equipos de red, periféricos, licencias u otros recursos.
2. **¿Quiénes utilizarán el sistema y qué permisos tendrá cada usuario?** Identificar administradores, técnicos de soporte, responsables del inventario y usuarios con equipos asignados.
3. **¿Qué información se registrará para cada activo?** Aclarar si incluirá código de identificación, número de serie, marca, modelo, fecha de adquisición, estado, ubicación, garantía y responsable.
4. **¿Qué operaciones podrá realizar el sistema?** Determinar si permitirá registrar, consultar, actualizar, asignar, trasladar, mantener y dar de baja equipos.
5. **¿Cómo se controlará la asignación de equipos a usuarios o departamentos?** Establecer cómo se registrarán entregas, devoluciones, transferencias y cambios de responsables.
6. **¿Cómo se manejarán los estados de los activos?** Definir si podrán clasificarse como disponibles, asignados, en mantenimiento, dañados o dados de baja.
7. **¿Cómo se evitarán los registros duplicados?** Aclarar si cada activo tendrá un código único, un número de serie obligatorio u otro mecanismo de identificación.
8. **¿Qué reportes necesitarán los responsables del inventario?** Determinar si se consultarán equipos por ubicación, responsable, estado, tipo de activo o fecha de adquisición.
9. **¿Se conservará el historial de cambios de cada activo?** Determinar si se registrarán asignaciones, mantenimientos, traslados, modificaciones y bajas.
10. **¿Qué funcionalidades entrarán en la primera versión y cuáles quedarán fuera?** Delimitar el alcance y priorizar las funciones esenciales para la primera entrega.

Estas preguntas son propuestas iniciales, no requisitos confirmados. Sus respuestas deben documentarse y utilizarse para ajustar la especificación y las decisiones posteriores.

## 6. Conclusión

Spec-Driven Development permite orientar el desarrollo de software a partir de necesidades explícitas, especificaciones verificables y decisiones documentadas. Ayuda a que los integrantes compartan una comprensión común del problema y evita que la implementación dependa exclusivamente de interpretaciones individuales.

GitHub Spec Kit facilita este enfoque mediante una estructura que relaciona los principios del proyecto, la especificación, la clarificación de dudas, la planificación técnica y la definición de tareas. En el proyecto de Inventario de TI, estos fundamentos ayudarán a comprender las necesidades de los actores, formular preguntas pertinentes y proporcionar una base clara para las etapas posteriores de diseño e implementación.