# Plan técnico 009

1. Reutilizar rutas/vistas históricas en v1 y registrar explícitamente el contrato OpenAPI.
2. Probar cobertura, compatibilidad, edición auditada, mantenimiento, licencias, roles y archivos.
3. Instrumentar log sanitizado con identificador; readiness SQL de solo lectura.
4. Separar etapas runtime/test y ejecutar pytest-django conservando regresión.
5. Modelar custodia primero en texto, luego BPMN 2.0.2/DI; contrastar OperationView/servicios/transacciones.
6. Consolidar C1-C3 en DSL y UML de clases/dependencias reales.
7. Preparar Quarto, CI y publicación manual de Pages desde gh-pages sin publicar.
8. Validar regresión, smoke, migraciones, restauración, exportación y presentación visual.

Principios aplicados: especificación antes de código; decisiones confirmadas; atomicidad/concurrencia; mínimo privilegio; historial; reproducibilidad; PR a develop. La constitución sigue siendo una propuesta documental y no se altera su estado.
