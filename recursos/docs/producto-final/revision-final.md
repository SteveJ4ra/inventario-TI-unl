# Revisión final del producto de Unidad 1

Validación de 002-009: base b60f52f, consolidación integrada por PR #33-35 en develop (04fa337864ba563c092944174a0368986c217336). Publicación manual en gh-pages, main intacta.

| Área | Resultado |
|---|---|
| Código/contratos | 378 pruebas y 284 subcasos correctos; 46 rutas/56 operaciones; 43 respuestas JSON validadas. |
| HTTP/runtime | 66 comprobaciones Gunicorn; exportación igual al esquema servido; rol SQL limitado y UID 10001. |
| Modelos | BPMN 2.0.2/XSD y DSL válidos; PlantUML regenerado y C3 con etiquetas legibles. |
| Operación | Migraciones coherentes; restauración temporal de 34 tablas/212 filas idénticas. |
| Linux/CI | ACL probada con UID 10001 y PostgreSQL 999; propietario conservado; otro UID no lee; sin lectura pública. |
| Portal | Quarto 1.11.9, nueve páginas, 395 enlaces locales correctos, sin imágenes rotas ni errores JavaScript. |
| API visual | Swagger muestra 56 operaciones y consulta autenticada; cuenta ficticia desactivada tras ensayo. |
| Presentación | Revisión de páginas PDF, tablas, comandos literales y diagramas; fuentes y edición de revisión identificadas. |

Integramos los PR [#33](https://github.com/SteveJ4ra/inventario-TI-unl/pull/33), [#34](https://github.com/SteveJ4ra/inventario-TI-unl/pull/34) y [#35](https://github.com/SteveJ4ra/inventario-TI-unl/pull/35) en develop. El [CI posterior al merge](https://github.com/SteveJ4ra/inventario-TI-unl/actions/runs/42335362951) completó 378 pruebas y 284 subcasos, migraciones, validadores y Quarto. [Portal técnico publicado](https://stevej4ra.github.io/inventario-TI-unl/). Pages sirve documentación estática; el backend funciona con Docker Compose local. Las fuentes históricas conservan sus fechas y estado, incluida la constitución PROPOSAL. No se agregan entrevistas, revisiones presenciales ni números de PR inexistentes.
