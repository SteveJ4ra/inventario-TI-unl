# Quickstart: validar 003

**Estado:** pasos de validación futura; implementación aún pendiente.

1. Migrar la base de datos de prueba desde una copia desechable.
2. Crear una facultad ficticia con operador y asignarla a un activo.
3. Crear una factura ficticia con dos activos, total común y valores por línea; comprobar el detalle sin duplicar total.
4. Registrar una donación con respaldo textual compartido y valor estimado por cada equipo.
5. Registrar adquisición con fecha desconocida y motivo; comprobar rechazo si falta el motivo.
6. Editar un campo descriptivo con motivo; verificar antes/después, autor/fecha y ficha actual.
7. Editar correo/nombre de custodio; verificar que movimientos anteriores mantienen snapshots originales.
8. Intentar cambiar ubicación o condición desde PATCH general; se rechaza.
9. Verificar permisos de gestor y operador; el gestor no puede administrar la lista de facultades.
10. Ejecutar validación automatizada de backend/frontend planificada en validation-plan.md al implementar.