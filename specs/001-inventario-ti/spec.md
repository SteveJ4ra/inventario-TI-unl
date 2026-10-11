# Especificación inicial — Inventario de Tecnologías de Información

**Proyecto:** Inventario de Tecnologías de Información (Proyecto N.º 2)
**Grupo:** N.º 5 — Universidad Nacional de Loja
**Estado:** Especificación inicial en revisión
**Identificador:** 001-inventario-ti

## 1. Contexto y problema

El proyecto busca organizar la información de los activos tecnológicos, incluyendo su ubicación, responsable o custodio, estado y movimientos registrados.

Uno de los aspectos principales es diferenciar los datos actuales de cada activo de los eventos ocurridos durante su ciclo de vida. De esta manera, se podrá conocer tanto la situación de un equipo como los cambios que ha tenido.

Actualmente no contamos con información suficiente para describir los procedimientos utilizados por la universidad para gestionar estos activos. Por ello, se trabajará con las necesidades identificadas en el enunciado del proyecto, sin asumir problemas que todavía no se han comprobado.

## 2. Objetivo

Definir los requisitos iniciales de un sistema que permita identificar individualmente los activos tecnológicos, consultar su situación actual y mantener un historial de sus movimientos, considerando las reglas y responsabilidades que se establezcan durante el desarrollo.

## 3. Alcance inicial

Para el primer incremento académico se propone trabajar con activos tecnológicos físicos y las siguientes funcionalidades:

- Registrar y consultar cada activo de manera individual.
- Consultar la ubicación, el custodio y el estado actual de un equipo.
- Registrar asignaciones, traslados, mantenimientos, novedades y bajas.
- Consultar el historial de movimientos de cada activo.
- Mantener coherencia entre la información actual y los movimientos registrados.
- Realizar pruebas con información ficticia o autorizada.

La cobertura institucional, las categorías de activos, los datos obligatorios y las reglas de autorización todavía deben definirse.

### 3.1. Funcionalidades fuera del alcance inicial

Para mantener un alcance manejable, no se contempla inicialmente desarrollar:

- Gestión completa de licencias de software.
- Control de ocupación de laboratorios.
- Administración detallada de reparaciones y costos.
- Descubrimiento automático de dispositivos en la red.
- Integración con otros sistemas institucionales.

La aplicación móvil, los códigos QR y la carga masiva de equipos se consideran posibles funcionalidades para etapas posteriores.

## 4. Actores del sistema

Se consideran tres perfiles principales para organizar las interacciones con el inventario.

| Actor | Necesidad | Interacción prevista |
|---|---|---|
| Gestor de activos | Mantener actualizada la información de los equipos | Registrar activos, consultar información y documentar movimientos |
| Custodio | Conocer los activos bajo su responsabilidad | Consultar asignaciones, comunicar novedades y confirmar recepciones cuando corresponda |
| Administrador | Supervisar el sistema y controlar los accesos | Administrar usuarios, roles y catálogos; consultar información general |

Los permisos y responsabilidades específicos deberán confirmarse antes de implementar el control de acceso.

## 5. Escenarios de usuario

### EU-P01. Consulta de situación actual

Como usuario autorizado, quiero consultar la ubicación, el custodio y el estado actual de un activo para conocer su situación.

### EU-P02. Registro individual de activos

Como gestor de activos, quiero registrar cada equipo con una identificación única para distinguirlo de otros equipos, incluso cuando tengan la misma marca y modelo.

### EU-P03. Consulta del historial

Como usuario autorizado, quiero consultar los movimientos de un activo para conocer los cambios realizados durante su ciclo de vida.

### EU-P04. Registro de movimientos

Como gestor de activos, quiero registrar los movimientos de un equipo para mantener actualizado su historial y su situación actual.

Estos escenarios podrán ajustarse cuando se definan las responsabilidades y reglas de operación.

## 6. Requisitos funcionales iniciales

| Código | Descripción | Estado |
|---|---|---|
| RF-P01 | Registrar e identificar individualmente cada activo tecnológico | Propuesto |
| RF-P02 | Consultar la situación actual de un activo | Propuesto |
| RF-P03 | Consultar el historial de movimientos de un activo | Propuesto |
| RF-P04 | Registrar movimientos relacionados con el ciclo de vida de los activos | Propuesto |
| RF-P05 | Mantener consistencia entre la información actual y el historial | Propuesto |
| RF-P06 | Controlar el acceso a las operaciones según los permisos establecidos | Pendiente de definición de permisos |

## 7. Requisitos de calidad

- **Integridad:** evitar contradicciones entre los datos actuales del activo y su historial.
- **Trazabilidad:** relacionar cada movimiento con el activo correspondiente.
- **Seguridad:** impedir que usuarios sin autorización modifiquen información.
- **Privacidad:** utilizar datos ficticios o autorizados durante las pruebas.
- **Verificabilidad:** comprobar las funcionalidades mediante criterios de aceptación y pruebas.
- **Mantenibilidad:** mantener una estructura de código clara, organizada y documentada.

Los valores específicos de rendimiento y disponibilidad se establecerán cuando se conozcan las necesidades del sistema.

## 8. Reglas de negocio pendientes

**RB-P01.** Definir el formato del identificador único de cada activo.

**RB-P02.** Establecer quién puede registrar, modificar, aprobar o corregir movimientos.

**RB-P03.** Definir los estados permitidos de un activo y las condiciones para cambiarlos.

**RB-P04.** Establecer los datos que se conservarán en el historial y el procedimiento para corregir errores.

**RB-P05.** Determinar si un activo puede permanecer temporalmente sin custodio o ubicación asignada.

## 9. Criterios de aceptación iniciales

### CA-P01. Identificación individual

- **Dado** un activo que ya tiene un identificador registrado.
- **Cuando** se intenta registrar otro activo con el mismo identificador.
- **Entonces** el sistema debe impedir que se duplique.

### CA-P02. Consulta de situación actual

- **Dado** un activo registrado y un usuario autorizado.
- **Cuando** el usuario consulta el activo.
- **Entonces** el sistema debe mostrar su ubicación, custodio y estado, según los permisos establecidos.

### CA-P03. Consulta del historial

- **Dado** un activo que tiene movimientos registrados.
- **Cuando** un usuario autorizado consulta su historial.
- **Entonces** el sistema debe mostrar los movimientos correspondientes.

### CA-P04. Consistencia de la información

- **Dado** un movimiento válido y autorizado.
- **Cuando** se registra el movimiento.
- **Entonces** la situación actual del activo debe mantenerse coherente con el cambio registrado.

Los criterios se ajustarán cuando se definan los campos obligatorios y las reglas de cada operación.

## 10. Casos especiales por analizar

- Consulta de un activo inexistente.
- Registro de identificadores duplicados.
- Activos sin custodio asignado.
- Movimientos realizados sin autorización.
- Corrección de información registrada anteriormente.
- Modificaciones simultáneas sobre un mismo activo.
- Consulta del historial de un activo dado de baja.

## 11. Clarificaciones pendientes

Antes de iniciar la implementación, es necesario definir algunos aspectos relacionados con los activos, las responsabilidades de los usuarios y los movimientos que registrará el sistema.

Las siguientes preguntas permitirán completar los requisitos y establecer las reglas de funcionamiento del inventario.

| Código | Pregunta de clarificación | Estado |
|---|---|---|
| Q01 | ¿Qué dependencias de la universidad y qué categorías de activos tecnológicos se incluirán inicialmente? | Pendiente |
| Q02 | ¿Qué información será obligatoria para registrar un activo y cómo se garantizará que su identificador sea único? | Pendiente |
| Q03 | ¿Qué usuarios podrán consultar, registrar, modificar y aprobar información o movimientos? | Pendiente |
| Q04 | ¿Qué diferencias existirán entre propietario, responsable y custodio de un activo? | Pendiente |
| Q05 | ¿Cómo se registrarán las asignaciones, devoluciones y traslados, y quién autorizará cada operación? | Pendiente |
| Q06 | ¿Qué estados podrá tener un activo y cuáles serán las condiciones para cambiar de estado o darlo de baja? | Pendiente |
| Q07 | ¿Qué movimientos y datos deberán conservarse en el historial y cómo se corregirán los registros incorrectos? | Pendiente |
| Q08 | ¿Qué consultas y reportes necesitarán los responsables del inventario? | Pendiente |
| Q09 | ¿Qué información se considera sensible y qué condiciones deberán aplicarse para protegerla y conservarla? | Pendiente |
| Q10 | ¿Será necesaria la integración con otros sistemas o bases de datos institucionales? | Pendiente |
| Q11 | ¿Se mantendrán los códigos QR y las funcionalidades móviles para etapas posteriores? | Pendiente |
| Q12 | ¿Cuáles serán las funcionalidades indispensables para completar el primer incremento académico? | Pendiente |

### 11.1. Registro de respuestas

Cuando se resuelva una pregunta, se registrará la respuesta, la fuente consultada y la fecha correspondiente. Las decisiones confirmadas se incorporarán a los requisitos, criterios de aceptación y documentos técnicos que resulten afectados.

Mientras no existan respuestas verificadas, las preguntas permanecerán pendientes. Las decisiones que afecten directamente la seguridad, los permisos o la consistencia de los movimientos deberán resolverse antes de implementar esas funcionalidades.

## 12. Trazabilidad inicial

| Fuente | Necesidad identificada | Requisito relacionado |
|---|---|---|
| Enunciado del proyecto | Identificar individualmente los activos | RF-P01 |
| Análisis y delimitación del problema | Conocer ubicación, custodio y estado | RF-P02 |
| Análisis del problema y ciclo de vida | Consultar los movimientos de un activo | RF-P03 |
| Alcance inicial del sistema | Registrar movimientos relevantes | RF-P04, RF-P05 |
| Identificación de actores | Diferenciar responsabilidades y accesos | RF-P06 |

## 13. Aspectos pendientes de validación

- [ ] Revisar y confirmar el alcance del primer incremento.
- [ ] Definir las categorías de activos y los campos obligatorios.
- [ ] Establecer los permisos de cada tipo de usuario.
- [ ] Acordar las reglas para registrar movimientos y cambiar estados.
- [ ] Resolver las preguntas que afecten las funcionalidades iniciales.
- [ ] Revisar los criterios de aceptación antes de implementar.

Esta especificación reúne las necesidades iniciales identificadas para el proyecto. Los requisitos y las reglas que siguen pendientes deberán revisarse con el grupo y, cuando corresponda, con el docente o los responsables institucionales.
