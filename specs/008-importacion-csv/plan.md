# Plan: importación CSV

## Enfoque

Mantener dos esquemas versionados: `assets-v1` y `license-lots-v1`. La API conserva el archivo temporal solo durante el flujo de revisión, protegida por autenticación, autorización y expiración de sesión/lote. Definir límites explícitos de bytes/filas en configuración; rechazar y explicar si se exceden.

## Flujo

1. Carga con tipo y plantilla/version.
2. Parseo CSV robusto y validación de cabeceras, codificación, filas y reglas de dominio.
3. Respuesta de vista previa completa; cero escrituras de dominio.
4. Primera confirmación autenticada del Gestor que cargó, sobre identificador y hash de vista previa.
5. Segunda confirmación explícita del mismo Gestor, sobre resumen final.
6. Transacción atómica; claves/constraints protegen duplicados concurrentes, códigos TI generados en servidor.

La vista previa expira y no es reutilizable después de aplicar/cancelar. La misma confirmación repetida debe ser idempotente y retornar el resultado existente, no duplicar el lote.

## Integración con dominio

Reutilizar validadores y servicios de 003/006, no duplicar reglas de negocio. Para documentos compartidos, deduplicar dentro del lote por tipo y referencia normalizada con validación de campos comunes (proveedor/fecha/total en compra); valores por activo siguen separados. Donación mantiene valor individual. Creación de activos siempre Disponible/sin custodio.

## Seguridad

Solo Gestores. Limitar tamaño/filas, escapar texto en vista previa, no interpretar fórmulas como HTML, impedir rutas de archivo, no persistir contenido tras vencimiento salvo que una auditoría técnica aprobada lo requiera. No añadir archivo original como documento histórico.
