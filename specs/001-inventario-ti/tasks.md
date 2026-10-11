# Tareas iniciales — Inventario de Tecnologías de Información

**Proyecto:** Inventario de Tecnologías de Información (Proyecto N.º 2)
**Grupo:** N.º 5 — Universidad Nacional de Loja
**Estado:** Planificación inicial de tareas
**Especificación:** `spec.md`
**Plan técnico:** `plan.md`
**Identificador:** 001-inventario-ti

## 1. Propósito

Organizar las tareas necesarias para continuar el desarrollo del sistema de Inventario de TI, tomando como referencia la especificación inicial, el plan técnico y las decisiones pendientes.

Las tareas se presentan por fases para facilitar el seguimiento del proyecto. Algunas corresponden a la preparación realizada durante la primera semana y otras deberán completarse antes de implementar las funcionalidades del sistema.

## 2. Fase 1. Preparación del proyecto

- [x] **T001.** Crear el repositorio remoto en GitHub y establecer las ramas `main` y `develop`.
- [x] **T002.** Definir el uso de ramas `feature/*` y Pull Requests para integrar los cambios.
- [x] **T003.** Preparar la documentación inicial del repositorio y las reglas de colaboración.
- [x] **T004.** Analizar el problema del Inventario de TI e identificar su alcance preliminar.
- [x] **T005.** Documentar los actores principales y sus interacciones propuestas.
- [x] **T006.** Documentar los fundamentos del desarrollo guiado por especificaciones.
- [x] **T007.** Seleccionar las tecnologías principales para el desarrollo del sistema.

## 3. Fase 2. Organización de Spec Kit

- [x] **T008.** Instalar y comprobar el funcionamiento de GitHub Spec Kit.
- [x] **T009.** Incorporar localmente las plantillas y scripts de Spec Kit.
- [x] **T010.** Preparar una constitución con principios de calidad, seguridad y colaboración.
- [x] **T011.** Elaborar la especificación inicial de los activos y sus movimientos.
- [x] **T012.** Registrar las preguntas de clarificación pendientes.
- [x] **T013.** Preparar el plan técnico inicial con las tecnologías acordadas.
- [ ] **T014.** Revisar los artefactos SDD y registrar las observaciones del grupo.
- [ ] **T015.** Integrar los archivos de Spec Kit a `develop` mediante Pull Request.

## 4. Fase 3. Preparación del entorno de desarrollo

- [ ] **T016.** Crear la estructura inicial del backend con Django.
- [ ] **T017.** Configurar un entorno virtual de Python y registrar las dependencias.
- [ ] **T018.** Preparar la configuración de PostgreSQL para el entorno local.
- [ ] **T019.** Incorporar Django REST Framework al proyecto.
- [ ] **T020.** Documentar en el README los pasos para instalar y ejecutar el backend.
- [ ] **T021.** Comprobar que otro integrante pueda reproducir la configuración siguiendo el README.

## 5. Fase 4. Revisión de requisitos

- [ ] **T022.** Confirmar los tipos de activos y sus datos obligatorios.
- [ ] **T023.** Definir las reglas de identificación individual y prevención de duplicados.
- [ ] **T024.** Revisar las responsabilidades y permisos de los perfiles del sistema.
- [ ] **T025.** Establecer los estados y movimientos permitidos.
- [ ] **T026.** Definir la información que debe conservarse en el historial.
- [ ] **T027.** Revisar los criterios de aceptación y actualizar la especificación.

## 6. Fase 5. Diseño e implementación

Las siguientes tareas dependen de la revisión de los requisitos correspondientes. No deben considerarse listas para implementar mientras existan decisiones que afecten sus reglas principales.

- [ ] **T028.** Diseñar los modelos de datos necesarios para los activos y sus relaciones.
- [ ] **T029.** Definir los recursos y operaciones de la API REST.
- [ ] **T030.** Implementar el registro individual de activos conforme a RF-P01.
- [ ] **T031.** Implementar la consulta de la situación actual conforme a RF-P02.
- [ ] **T032.** Implementar la consulta del historial conforme a RF-P03.
- [ ] **T033.** Implementar el registro de movimientos conforme a RF-P04.
- [ ] **T034.** Comprobar la consistencia entre información actual e historial conforme a RF-P05.
- [ ] **T035.** Aplicar los permisos definidos para las operaciones del sistema conforme a RF-P06.
- [ ] **T036.** Preparar pruebas relacionadas con los criterios de aceptación aprobados.

## 7. Dependencias principales

| Actividad | Depende de |
|---|---|
| Integración de Spec Kit | Revisión de los documentos SDD |
| Preparación del backend | Entorno Python, dependencias y configuración inicial |
| Modelos de datos | Definición de campos, identificadores y reglas del dominio |
| Registro de movimientos | Reglas de estados, autorizaciones e historial |
| Control de acceso | Definición de usuarios y permisos |
| Pruebas funcionales | Requisitos y criterios de aceptación revisados |
| Integración web y móvil | Servicios backend disponibles y contratos definidos |

## 8. Seguimiento de las tareas

El avance del proyecto se registrará mediante commits, Pull Requests y revisiones en GitHub.

Una tarea se marcará como completada únicamente cuando exista evidencia suficiente de su realización. Las tareas de implementación deberán relacionarse con los requisitos y criterios de aceptación correspondientes.

Las actividades pendientes podrán ajustarse cuando se resuelvan las clarificaciones y se definan las prioridades del siguiente incremento.
