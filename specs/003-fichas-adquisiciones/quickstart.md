# Quickstart: validar 003

**Estado:** pasos de validación futura; implementación aún pendiente.

1. Migrar la base de datos de prueba desde una copia desechable.
2. Provisionar operador con create_operator; iniciar sesión sin permisos de Gestor, crear facultad y probar su cambio auditado.
3. Crear metadatos de factura; registrar dos activos usando su id compartido, total común y valores por línea; comprobar atomicidad y que no se duplica el total.
4. Registrar una donación con respaldo textual compartido y valor estimado por cada equipo.
5. Registrar adquisición con fecha desconocida y motivo; comprobar rechazo si falta el motivo.
6. Editar un campo descriptivo con motivo; verificar antes/después, autor/fecha y ficha actual.
7. Editar correo/nombre de custodio; verificar que movimientos anteriores mantienen snapshots originales.
8. Intentar cambiar ubicación o condición desde PATCH general; se rechaza.
9. Verificar permisos de gestor y operador; el gestor no puede administrar la lista de facultades.
10. Ejecutar validación automatizada de backend/frontend planificada en validation-plan.md al implementar.

Antes de ejecutar Spec Kit, seleccionar `specs/003-fichas-adquisiciones` siguiendo [el índice SDD](../../docs/sdd/README.md#seleccionar-el-paquete-correcto-en-spec-kit) y verificar FEATURE_DIR. El chequeo solo verifica documentos; no ejecuta implementación ni pruebas de aceptación.
