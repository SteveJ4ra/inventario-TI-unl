# Guía de contribución

Este documento establece las pautas básicas para colaborar en el proyecto **Inventario de Tecnologías de Información**, desarrollado por los integrantes del grupo.

## 1. Estrategia de ramas

El proyecto utiliza las siguientes ramas:

- `main`: contiene las versiones estables del proyecto.
- `develop`: permite integrar y revisar los cambios realizados por el equipo.
- `feature/*`: ramas temporales destinadas al desarrollo de tareas específicas.

Las nuevas ramas de trabajo deben crearse a partir de `develop`.

## 2. Flujo de trabajo

Cada integrante debe seguir estos pasos:

1. Actualizar la rama `develop` desde el repositorio remoto.
2. Crear una rama `feature/*` con un nombre descriptivo.
3. Realizar los cambios correspondientes a su tarea.
4. Registrar los cambios mediante commits.
5. Publicar la rama en GitHub.
6. Crear un pull request dirigido a `develop`.
7. Solicitar la revisión de otro integrante antes de integrar los cambios.

Después de integrar una rama, esta podrá eliminarse si ya no es necesaria.

## 3. Convención de commits

Los mensajes deben describir de manera clara los cambios realizados.

Se recomienda utilizar los siguientes prefijos:

- `feat:` nueva funcionalidad.
- `fix:` corrección de errores.
- `docs:` cambios en documentación.
- `chore:` configuración o mantenimiento.
- `refactor:` reorganización del código sin modificar su comportamiento.
- `test:` incorporación o modificación de pruebas.

Ejemplos:

`docs: agregar análisis del problema`

`feat: implementar registro de activos`

`fix: corregir validación de campos`

## 4. Revisión de contribuciones

Antes de integrar cambios en `develop`, otro integrante debe revisar el pull request para comprobar que:

- Los cambios corresponden a la tarea propuesta.
- No se modifican archivos ajenos sin justificación.
- La documentación es clara y está actualizada cuando corresponde.
- No se incluyen archivos innecesarios ni información sensible.

Los cambios hacia `main` se realizarán cuando el equipo considere que existe una versión estable.

## 5. Consideraciones generales

- Mantener una comunicación clara entre los integrantes.
- Evitar trabajar directamente sobre `main` y `develop`.
- No subir contraseñas, tokens, credenciales ni datos institucionales confidenciales.
- Registrar contribuciones identificables mediante commits.
- Mantener la organización del repositorio conforme evolucione el proyecto.