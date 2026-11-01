# Plan de validación: 005

**Estado:** por ejecutar.

- Matriz: Gestor/Reviewer/Operator/anónimo/inactivo.
- Bajas normales: condición cualquiera permitida, ubicación, Disponible, no custodio, sin mantenimiento; motivo obligatorio.
- Bajas No localizado: solicitud asignada a otra facultad; no autoaprobación; decisión una vez.
- Rechazo y re-solicitud; motivo obligatorio.
- Recuperación cancela pendiente y graba motivo/actor/fecha.
- Reviewer no lista activos ni opera; password temporal bloquea funciones hasta cambio.
- Reasignar todas pendientes antes de desactivar reviewer.
- Desactivar Gestor conserva autoría.
- Concurrencia: doble solicitud/decisión/baja no duplica transiciones.
- Ejecutar pruebas y revisión de privacidad después de implementación; no hay resultados todavía.

## Casos de integración de revisión final

Revisor temporal no usa API antes de cambio inicial; Operador puede reasignar y Gestor no. Probar carrera recuperación/aprobación, desactivación/reasignación y facultad/decisión. Rectificar baja enlazada restaura snapshot sin borrar solicitud/decisión.
