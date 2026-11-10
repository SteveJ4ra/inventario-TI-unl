# Investigación: novedades y mantenimiento

El flujo reutiliza la arquitectura y stack de 002. La decisión de mantener historial append-only y separar condición/ubicación del evento proviene de las decisiones funcionales del propietario; no se introduce un estándar externo como política de la UNL.

Los cambios de ubicación al inicio y cierre de mantenimiento, pérdida y recuperación son operaciones de ciclo de vida explícitamente aceptadas. No se agrega catálogo ni integración de ubicaciones.
