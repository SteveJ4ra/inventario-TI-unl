# Quickstart: validar 006

**Pendiente de implementación.**

1. Crear un lote USER_SEAT de 10 unidades, 4 en uso y fecha de inicio pasada; verificar 6 remanentes y Vigente.
2. Cambiar fecha de fin a fecha pasada; verificar Vencido y 6 remanentes.
3. Intentar omitir fecha inicial; rechazo.
4. Omitir fecha final; el lote no vence automáticamente.
5. Intentar registrar 11 en uso para 10 compradas; rechazo sin auditoría ni cambio.
6. Editar a 3 en uso; verificar 7 remanentes e historial.
7. Crear DEVICE_SEAT; comparar filtros y búsqueda.
8. Verificar un usuario no gestor; acceso denegado.