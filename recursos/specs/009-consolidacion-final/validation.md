# Validación 009

| Comprobación | Resultado local |
|---|---|
| pytest/pytest-django sobre PostgreSQL aislado | 378 pruebas, 284 subcasos, sin fallos ni advertencias; incluye 37 pruebas de dominio aislado. |
| Contrato v1 | 46 rutas/56 operaciones; correspondencia exacta con vistas/métodos. |
| OpenAPI | 3.1 válido; exportación igual al runtime; 43 respuestas JSON reales sin errores de esquema. |
| HTTP Gunicorn | 66 comprobaciones: flujo principal, módulos adicionales, permisos, sesión y límite de intentos. |
| Migraciones | No changes detected. |
| Privilegios | UID 10001; rol operativo sin superusuario, CREATEDB o CREATEROLE. |
| BPMN | XML/DI válidos frente a XSD OMG 2.0.2; entradas/salidas y compuertas comprobadas. |
| C4/UML | DSL válido; cuatro figuras PlantUML regeneradas. |
| Respaldo | 34 tablas/212 filas con SHA-256 idéntico en restauración temporal; original conservada. |

Fuentes reproducibles, comandos y hashes: docs/producto-final/evidencia-validacion.json. El portal y PDF se comprueban visualmente al cerrar el paquete de entrega y se documentan en docs/producto-final/revision-final.md. Los resultados son locales: no declaran despliegue de Pages ni ejecución remota de Actions. El informe no certifica carga, pentesting externo o producción institucional.
