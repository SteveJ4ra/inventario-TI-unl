# Plan técnico inicial — Inventario de Tecnologías de Información

**Proyecto:** Inventario de Tecnologías de Información (Proyecto N.º 2)
**Grupo:** N.º 5 — Universidad Nacional de Loja
**Estado:** Plan técnico preliminar
**Especificación relacionada:** `spec.md`
**Identificador:** 001-inventario-ti

## 1. Propósito

Este plan establece las tecnologías, la organización general y las actividades técnicas previstas para desarrollar el sistema de Inventario de TI.

La planificación se basa en los requisitos iniciales y en los acuerdos tecnológicos del grupo. Algunos aspectos del funcionamiento del sistema todavía deben aclararse antes de definir la implementación de cada módulo.

## 2. Tecnologías seleccionadas

El grupo acordó utilizar las siguientes tecnologías:

| Componente | Tecnología | Uso previsto |
|---|---|---|
| Lenguaje del backend | Python | Desarrollo de la lógica del servidor |
| Framework backend | Django | Organización del proyecto y gestión de datos |
| API | Django REST Framework | Desarrollo de servicios REST |
| Base de datos | PostgreSQL | Almacenamiento de información del inventario |
| Interfaz web | React + TypeScript | Aplicación web para interactuar con el sistema |
| Aplicación móvil futura | React Native + Expo + TypeScript | Acceso móvil en una etapa posterior |
| Control de versiones | Git y GitHub | Trabajo colaborativo y revisión de cambios |
| Desarrollo guiado por especificaciones | GitHub Spec Kit | Organización de requisitos, planificación y tareas |

Estas tecnologías representan la decisión técnica del grupo. Su selección no implica que todos los componentes ya estén instalados o implementados.

## 3. Organización técnica propuesta

Se propone comenzar con un backend desarrollado en Django y Django REST Framework, conectado a PostgreSQL.

Para mantener el proyecto organizado, se separarán las responsabilidades principales:

- **Acceso mediante API:** recepción de solicitudes y entrega de respuestas.
- **Reglas del sistema:** validaciones y operaciones relacionadas con los activos.
- **Persistencia:** almacenamiento y consulta de información.
- **Control de acceso:** verificación de usuarios y permisos según las reglas que se definan.

La aplicación web consumirá los servicios del backend. La aplicación móvil se considerará en una etapa posterior, reutilizando los servicios que resulten adecuados.

Esta organización es una propuesta inicial. La estructura definitiva de módulos y componentes se establecerá conforme se precisen los requisitos.

## 4. Información principal del sistema

De acuerdo con el problema planteado, el sistema deberá trabajar con información relacionada con:

- Activos tecnológicos.
- Ubicaciones.
- Responsables o custodios.
- Estados de los activos.
- Movimientos e historial.

La identificación individual de los activos será un aspecto central del diseño.

Antes de crear los modelos de datos se deberán definir los campos obligatorios, las relaciones, los estados permitidos y las condiciones para registrar o corregir movimientos.

Por ahora no se establecen tablas, cardinalidades ni restricciones específicas de PostgreSQL.

## 5. Desarrollo de la API

El backend expondrá las funcionalidades que sean necesarias para cumplir los requisitos aprobados.

Inicialmente se consideran las siguientes áreas:

- Registro y consulta de activos.
- Consulta de su situación actual.
- Registro de movimientos.
- Consulta del historial.
- Control de acceso según los permisos definidos.

Los recursos, endpoints, métodos HTTP, validaciones y formatos de respuesta se definirán durante el diseño de cada funcionalidad.

Cuando corresponda, se documentará la API para facilitar su integración y comprobación.

## 6. Criterios de calidad y seguridad

Durante el desarrollo se tendrán en cuenta los siguientes criterios:

**Organización del código:** mantener responsabilidades claras y evitar concentrar toda la lógica en un solo componente.

**Mantenibilidad:** utilizar nombres comprensibles, funciones organizadas y documentación necesaria para el equipo.

**Validación:** comprobar que los datos recibidos y las operaciones ejecutadas cumplan las reglas definidas.

**Trazabilidad:** asegurar que los movimientos registrados puedan relacionarse con los activos correspondientes.

**Seguridad:** proteger las operaciones que requieran autorización y evitar publicar contraseñas, claves o información sensible en GitHub.

**Pruebas:** comprobar las funcionalidades mediante pruebas acordes con sus requisitos y criterios de aceptación.

Se podrán aplicar principios de programación orientada a objetos y SOLID cuando aporten claridad al diseño, sin introducir clases o abstracciones innecesarias. No se establece TDD como una obligación del proyecto.

## 7. Entorno de desarrollo y colaboración

El código se administrará mediante Git y GitHub.

Se utilizará la siguiente estrategia de ramas:

- `main`: versiones estables.
- `develop`: integración de los avances revisados.
- `feature/*`: desarrollo de funcionalidades y documentación específica.

Los cambios se incorporarán mediante commits y Pull Requests, con revisión antes de integrarse a `develop`.

Para el backend se utilizará un entorno virtual de Python y un archivo de dependencias que permita reproducir la instalación. El README deberá contener los pasos necesarios para preparar y ejecutar el proyecto.

La configuración se verificará en otro entorno antes de considerarla reproducible.

## 8. Etapas de trabajo previstas

### Etapa 1. Preparación del proyecto

- Configurar el repositorio y las ramas de colaboración.
- Incorporar la estructura de GitHub Spec Kit.
- Documentar el problema, los actores y el alcance.
- Establecer la constitución y especificación inicial.
- Preparar el entorno de desarrollo del backend.

### Etapa 2. Revisión de requisitos

- Revisar las preguntas de clarificación pendientes.
- Definir los datos obligatorios de los activos.
- Establecer los permisos y responsabilidades.
- Precisar las reglas de movimientos y estados.
- Revisar los criterios de aceptación.

### Etapa 3. Diseño del backend

- Definir la organización de las aplicaciones Django.
- Diseñar los modelos de datos necesarios.
- Establecer validaciones y reglas del sistema.
- Definir los recursos de la API REST.
- Preparar las pruebas iniciales.

### Etapa 4. Implementación y comprobación

- Implementar las funcionalidades priorizadas.
- Comprobar el registro y la consulta de activos.
- Verificar la trazabilidad de movimientos.
- Probar validaciones y permisos.
- Documentar los resultados y corregir los errores encontrados.

### Etapa 5. Integración de interfaces

- Preparar la interfaz web con React y TypeScript.
- Conectar la interfaz con los servicios disponibles.
- Evaluar posteriormente las funcionalidades móviles previstas con React Native y Expo.

Estas etapas indican el orden general de trabajo. No representan actividades finalizadas ni fechas de entrega confirmadas.

## 9. Riesgos técnicos y medidas preventivas

| Riesgo | Medida prevista |
|---|---|
| Requisitos incompletos | Revisar las clarificaciones antes de implementar funciones dependientes |
| Inconsistencia entre activos y movimientos | Definir validaciones y comprobar los cambios mediante pruebas |
| Permisos indefinidos | Establecer responsabilidades antes de habilitar operaciones restringidas |
| Problemas de integración entre componentes | Documentar y probar la API de forma progresiva |
| Dificultades para reproducir el entorno | Mantener instrucciones y dependencias actualizadas |
| Crecimiento innecesario del proyecto | Priorizar las funcionalidades del primer incremento |

## 10. Decisiones pendientes

Antes de completar el diseño técnico deberán resolverse los siguientes aspectos:

- Campos obligatorios e identificación única de activos.
- Reglas para registrar asignaciones, traslados y bajas.
- Estados permitidos y condiciones de cambio.
- Responsabilidades y permisos de cada perfil.
- Información requerida en el historial.
- Consultas y reportes indispensables.
- Estructura definitiva de módulos y modelos de datos.
- Estrategia de pruebas para las funcionalidades priorizadas.

Estas decisiones se relacionan con las clarificaciones registradas en `spec.md` y deberán actualizarse conforme se obtengan respuestas.

## 11. Resultado esperado

El resultado esperado es disponer de un backend organizado y comprobable que permita gestionar la información básica de los activos tecnológicos y mantener trazabilidad de sus movimientos.

La implementación se desarrollará progresivamente, utilizando las especificaciones y los criterios de aceptación como referencia para planificar las tareas y verificar los resultados.
