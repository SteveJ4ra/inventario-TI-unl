# Implementación 009

## Contrato

urls_v1 comparte urlpatterns con las rutas históricas. openapi_contract deriva tipos DRF y especializa reglas entre campos, respuestas compuestas y relaciones ReadOnly/nulabilidad. openapi_v1 sirve el esquema y conserva Swagger/live.js. export_openapi genera el documento sin conexión SQL. La exportación canónica es docs/producto-final/openapi.json.

## Observabilidad y disponibilidad

RequestLoggingMiddleware asigna X-Request-ID y registra método/ruta resuelta/estado/duración; JsonRequestFormatter emite JSON sin cuerpos, query o cookies. /health/ready/ hace SELECT 1 y responde 200/503 sin configuración; Docker usa esa ruta. No se crean tablas ni cambian reglas de negocio.

## Pruebas y operación

ContractClient verifica respuestas reales con JSON Schema; CompleteV1Tests compara rutas/métodos y cubre edición, mantenimiento, licencias, permisos, HEAD/405 y archivos. ObservabilityTests verifica fallo SQL genérico y exclusión de datos sensibles. La imagen test añade pytest-django/jsonschema; runtime no instala esas dependencias. Se conserva manage.py test.

El smoke amplía el recorrido protegido a 66 comprobaciones HTTP. backup_roundtrip compara contenido restaurado en una base temporal propia y no sobrescribe la original. Sus resultados/dumps se mantienen ignorados.

## Artefactos

BPMN con DI y SVG/PNG; C4 DSL y PlantUML; portal Quarto; CI de validación y publicación manual en gh-pages desde fuentes develop. La publicación se realiza después de revisión por ramas/PR a develop. Los resultados se registran en validation.md y docs/producto-final/evidencia-validacion.json.
