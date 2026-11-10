# Correspondencia con el producto final de Unidad 1

| Criterio solicitado | Artefacto | Comprobación y alcance |
|---|---|---|
| Problema, actores y alcance | docs/analisis; portal/index.qmd | Propuesta académica basada en el tema 2, sin atribuir procesos internos no investigados. |
| SDD, historias y aceptación | specs/002-009; portal/sdd.qmd | 104 RF de negocio y seis de consolidación técnica; decisiones/planes/tareas/implementación/validación. |
| BPMN 2.0.2 | proceso-custodia.md; custodia.bpmn, svg y png | Texto previo, calles, tareas en infinitivo, decisiones/excepciones y DI; XSD OMG válido. |
| C4 y UML | arquitectura.dsl; cuatro puml/png | C1/C2/C3 y clases/dependencias del flujo; DSL validado. |
| Decisiones | ADR de S3/S4/S5 y ADR-0901 | Monolito, contrato, seguridad, despliegue y consolidación explicados. |
| REST, versión y contrato | openapi.json; backend/inventory/openapi_contract.py | 46 rutas/56 operaciones; envoltura JSON y excepciones de archivo/HTTP. |
| Seguridad | Modelo de amenazas S4; portal/seguridad.qmd | Roles, CSRF, sesión absoluta, límite de intentos, entrada estricta, secretos y mínimo privilegio. |
| Pruebas | inventory/tests, isolated_tests, contract_tests | 378 pruebas y 284 subcasos; SQL real y dominio aislado. |
| Git/colaboración | Historial y PR #14-18, #20-32 según integración | Aportes verificables por integrante; consolidación integrada mediante PR #33-35 a develop. |
| Quarto | portal/ y publicación manual en gh-pages | [Portal HTTPS activo](https://stevej4ra.github.io/inventario-TI-unl/); fuentes en develop. |
| Docker/CI | Dockerfile, compose.yaml, workflows | Runtime/test separados, PostgreSQL y scripts; [CI remoto correcto](https://github.com/SteveJ4ra/inventario-TI-unl/actions/runs/42335362951). |
| Observabilidad | observability.py y health/ready | Logs sanitizados, request_id, estado/duración y SQL de disponibilidad. |
| Demostración | operacion-ampliada.md y deploy/smoke.py | Flujo real de extremo a extremo, no presentación de mocks. |
| Contribución/reflexión/IA | portal/equipo.qmd e informe | Seis perspectivas vinculadas a PR reales; uso de IA y fuentes declarados. |
