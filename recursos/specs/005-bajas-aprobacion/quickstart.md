# Quickstart: validar 005

**Pendiente de implementación.** Usar DB/usuarios ficticios.

1. Dar de baja activo Disponible sin custodia y con motivo; comprobar registro conservado.
2. Intentar baja sin motivo, Asignado, No localizado o mantenimiento activo; todas se rechazan por la regla apropiada.
3. Cerrar mantenimiento con resultado antes de baja normal.
4. Reportar activo perdido y crear solicitud asignada a reviewer de otra facultad.
5. Comprobar que el solicitante no puede aprobar y reviewer no ve activos fuera de sus solicitudes.
6. Rechazar con motivo; comprobar estado No localizado e historial.
7. Crear nueva solicitud con motivo actualizado.
8. Crear otra solicitud, recuperar activo antes de decisión y verificar cancelación con motivo.
9. Intentar desactivar reviewer con solicitud pendiente; reasignar y volver a desactivar.
10. Cambiar contraseña temporal en primer login; probar que antes del cambio solo se permite consultar sesión, cerrar sesión y cambiar contraseña.
11. Desactivar Gestor por comando y verificar que su autoría previa permanece.

Antes de ejecutar Spec Kit, seleccionar `specs/005-bajas-aprobacion` siguiendo [el índice SDD](../../docs/sdd/README.md#seleccionar-el-paquete-correcto-en-spec-kit) y verificar FEATURE_DIR. El chequeo solo verifica documentos; no ejecuta implementación ni pruebas de aceptación.
