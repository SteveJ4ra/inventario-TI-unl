# Contrato web: CSV

1. Elegir «Activos» o «Lotes de licencias» y descargar la plantilla correspondiente.
2. Cargar archivo; mostrar progreso/error sin perder contexto.
3. Mostrar todas las filas válidas y errores con fila/campo/motivo; si existe error, no habilitar confirmación.
4. Lote válido: mostrar contenido completo paginado sin omitir filas, resumen total y advertencia de creación masiva.
5. Primera confirmación explícita; luego confirmación final que muestra nuevamente tipo y número de registros.
6. Durante aplicación, evitar doble envío; mostrar resultado por conteos y referencia del lote.
7. Cancelación, expiración o error no deja escrituras parciales; proporcionar descarga/listado de errores para corregir.
