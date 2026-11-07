# Contratos web: licencias

- Vista listada de lotes con producto, proveedor, tipo, compradas, en uso, remanentes, vigencia/estado.
- Formulario de alta y edición; el campo fecha de inicio es obligatorio y la fecha de fin opcional.
- Al modificar cantidades, la interfaz muestra la diferencia calculada; backend vuelve a validar.
- Un lote vencido conserva el número remanente y se etiqueta Vencido; no mostrarlo como disponibilidad vigente.
- El formulario no contiene campos de clave, usuario destino o equipo destino.
- Cambios de cantidad muestran historial de quién/cuándo/antes/después.

## Pantalla entregada

Acceso desde el botón Licencias de la navegación existente, también visible a 375px. Listado, filtros combinables, limpieza y páginas; formulario de alta y edición con los siete campos canónicos. Se muestran carga, resultado vacío y fallo de red como estados diferentes, con consulta manual de nuevo cuando corresponde.

Detalle incluye remanentes, etiqueta temporal y auditoría paginada de alta/ediciones con autor registrado, fecha, revisión y los siete valores antes/después. Las horas históricas se presentan en America/Guayaquil; las fechas de vigencia conservan su día ISO. El cliente no decide la vigencia: usa la respuesta del backend.

El botón Guardar se deshabilita durante el envío. PATCH incluye expected_revision de la ficha vista y usa el cliente compartido de sesión/CSRF. Ante 409 se cierra el formulario obsoleto, se recarga ficha/historial y se muestra que debe revisarse antes de volver a editar; no se repite el PATCH. Errores de campo se muestran con etiquetas en español. Logout o sesión 403 desmonta la vista privada.

React representa producto, proveedor y snapshots como texto. No hay campo de claves, facturas o destinatarios individuales ni edición/borrado del historial.
