# Plan de validación: importación CSV

**Estado: pendiente; sin pruebas ejecutadas.**

- Unitarias: cabeceras/versiones, tipos, campos condicionales, fechas, cantidades y normalización.
- Integración: preview sin escrituras, dos confirmaciones, hash, acceso y CSRF, expiración y cancelación.
- Atomicidad: fallar una fila al aplicar deja cero activos/lotes; reintento no duplica.
- Casos de dominio: factura/respaldo compartido con valores individuales; códigos TI automáticos; inicio de licencia obligatorio; disponible calculado.
- Frontend: errores legibles, vista previa y ambas confirmaciones.
- Evidencia: resultados automáticos y registro manual de aceptación.

## Casos de integración de revisión final

Aplicar simultáneamente el mismo lote crea una sola vez; repetir devuelve 200. Cambio concurrente en documento/facultad/identidad tras preview rechaza todo sin datos parciales. Preview conserva filas normalizadas y propietario.
