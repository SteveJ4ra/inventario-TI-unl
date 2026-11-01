# Especificación: importación CSV de activos y licencias

**Rama propuesta:** feature/importacion-csv
**Identificador:** 008-importacion-csv
**Estado:** especificación preparada; no implementada.
**Decisiones:** DBE-034 a DBE-036, DBE-046.

## Descripción

Permitir a Gestores cargar un CSV de activos físicos o un CSV distinto de lotes de licencias. El sistema valida el documento completo, presenta vista previa y errores, y crea el lote entero o nada tras dos confirmaciones explícitas.

## Historias y aceptación

### US1 — Importar activos (P1)
1. La plantilla incluye los campos de ficha y adquisición definidos en 003; campos condicionales siguen reglas Compra/Donación y fecha desconocida con motivo.
2. El código TI lo genera el servidor. Cada activo inicia Disponible y sin custodio.
3. Documentos de compra o respaldo de donación repetidos se vinculan como un único documento compartido; valor individual permanece en cada fila.

### US2 — Importar lotes de licencias (P1)
1. Plantilla separada; cada fila representa un lote, nunca una licencia/asiento individual.
2. Incluye software, proveedor, tipo, cantidades, fecha de inicio obligatoria y fecha de fin opcional.
3. Valida las reglas de 006, incluyendo cantidad en uso no superior a comprada.

### US3 — Vista previa y confirmación (P1)
1. Se validan todas las filas y se muestran errores por número de fila/campo.
2. Si hay al menos un error, se rechaza el archivo completo y no hay confirmación de creación.
3. Un lote válido muestra vista previa completa/resumen; requiere primera confirmación y confirmación final que repite cantidad y tipo de registros.
4. La aplicación crea todo de forma atómica; fallo en cualquier registro deja cero registros creados.
5. Las confirmaciones quedan asociadas a la misma vista previa inmutable y las completa el mismo Gestor que cargó el lote; cambios al archivo requieren nueva carga/validación.

## Requisitos funcionales

- FR-001: aceptar CSV de activos físicos y lotes de licencias mediante plantillas separadas y versionadas.
- FR-002: validar el archivo completo y mostrar todos los errores por fila/campo antes de escribir datos.
- FR-003: ante cualquier error, rechazar el lote entero y crear cero registros de dominio.
- FR-004: presentar una vista previa completa y resumen de los registros válidos.
- FR-005: exigir dos confirmaciones explícitas del mismo Gestor que inició el lote.
- FR-006: vincular confirmaciones a una vista previa inmutable identificada por lote/hash.
- FR-007: aplicar activos o lotes en una transacción atómica, sin resultados parciales.
- FR-008: generar código TI en servidor y crear activos importados como Disponibles/sin custodio.
- FR-009: respetar reglas de adquisición de compra/donación y documentos compartidos de 003.
- FR-010: tratar cada fila de licencias como un lote, aplicando reglas de fecha y cantidad de 006.
- FR-011: hacer idempotente el reintento de aplicación del mismo lote ya aplicado.
- FR-012: rechazar archivo que exceda límites técnicos configurados; nunca truncar ni importar parcialmente.

## Criterios de éxito

- SC-001: una carga con errores en varias filas lista todos los errores y no crea ningún registro.
- SC-002: un archivo válido exige dos confirmaciones del mismo Gestor y queda ligado al preview revisado.
- SC-003: si la aplicación falla en una fila, se revierten todas las escrituras del lote.
- SC-004: reintentar aplicación ya completada devuelve el resultado previo sin duplicados.
- SC-005: activos creados reciben códigos TI nuevos y quedan Disponibles/sin custodio.
- SC-006: las plantillas de activo y licencia validan sus campos condicionales, inicio de vigencia incluido.

## Límites

Sin importación parcial, custodios, movimientos, baja, novedades, QR o asignaciones de licencias; sin XLSX. Los tamaños máximos y límites de filas son parámetros técnicos que deben fijarse en implementación antes de habilitar el servicio; la especificación funcional no autoriza truncar o procesar parcialmente.
