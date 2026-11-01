# Plan de validación: 003

**Estado:** por ejecutar tras implementación.

- Contratos API: compra con una y varias líneas; documento de donación compartido; valores por activo.
- Integridad: documento/lineas guardados juntos; duplicidad de activo no deja datos parciales.
- Edición: reason requerido; snapshots antes/después con actor y hora; campos de estado no aceptados.
- Historial: edición de custodio no cambia datos de movimientos ya ocurridos.
- Acceso: gestor, operador, anónimo y usuario no autorizado.
- Migración: conservar datos previos; no inventar faculty/origen/fecha.
- Web: formularios, errores por campo, auditoría visible, no selector de divisa.
- Ejecución final pendiente; ningún resultado se declara aprobado.

## Casos de integración de revisión final

Operador inicia sesión antes de 005 sin obtener permiso Gestor; prueba alta de documento sin activos y alta atómica activo+línea; fallos revierten ambos. Ediciones incrementan revisión e impiden rectificar movimientos anteriores. Migración usa mapeo verificado, no fixtures.
