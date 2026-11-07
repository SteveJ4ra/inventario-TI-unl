# Estándares y decisiones de interoperabilidad

La interoperabilidad depende de respetar contratos observables; no basta que dos componentes estén escritos en Python. Distinguimos estándares de intercambio de convenciones internas y de herramientas de ejecución.

| Referencia | Aplicación concreta | Evidencia | Límite interpretado |
| --- | --- | --- | --- |
| HTTP, RFC 9110 | GET consulta sin mutar, POST registra operaciones y PATCH corrige datos autorizados; códigos 200/201, 400, 403, 404 y 409 coherentes | Catálogo de rutas, test_api_v1.py, contract_tests/test_api.py y recorrido HTTP | La autenticación de sesión utiliza 403 en rechazos; no se afirma que siempre devuelva 401 |
| JSON, RFC 8259 | Cuerpos y respuestas JSON; propiedades y tipos definidos, rechazo de formatos inesperados | Serializadores, pruebas de JSON malformado y sobre v1 | JSON válido no garantiza cumplimiento de una regla de custodia o permiso |
| OpenAPI 3.1.0 | Esquema servido y exportado del recorrido /api/v1/, con parámetros, cuerpos, errores y seguridad por cookie/CSRF | openapi_v1.py, docs/semana-3/openapi-v1.json y pruebas del esquema | Diez paths de v1; el catálogo de 59 patrones y contratos complementa los módulos /api/ |
| WSGI, PEP 3333 | Separación del servidor HTTP y la aplicación Django | config.wsgi:application ejecutada por Gunicorn | No añade por sí solo autorización ni TLS |
| Dockerfile y Compose | Construcción, redes, healthchecks, dependencias, secretos y volumen definidos | ADR-0501 y compose.yaml | Especificación de contenedores/configuración, no un estándar de negocio ni garantía universal de portabilidad |
| OWASP y guía Django de despliegue | Riesgos de acceso, sesión, caché, secretos y configuración | Controles de semana 4 y seis pruebas de despliegue/QR | Guías de seguridad, no certificación ni reemplazo de una política institucional |
| SDD y flujo Git del equipo | Decisiones, especificación, plan, tareas, pruebas y revisión rastreables | specs/002-008, matriz, bitácora y PR históricos | Método y convención de colaboración; no son un protocolo de interoperabilidad |

## Interpretación en el proyecto

Elegimos mantener /api/ para no romper los clientes existentes y versionar el recorrido base en /api/v1/. El sobre success/message/data/errors/meta pertenece a v1; obligar retroactivamente a todos los módulos a usarlo cambiaría contratos y clientes sin una necesidad confirmada. El catálogo explicita esa diferencia.

La sintaxis JSON, un código HTTP correcto y un esquema legible ayudan a integrar clientes. La integridad depende además de transacciones y restricciones en PostgreSQL: dos entregas simultáneas no deben producir dos custodias vigentes y una importación no debe escribir solo parte de un lote. La matriz relaciona estas reglas con pruebas de concurrencia y rollback.

Las fechas de intercambio y los importes conservan las representaciones fijadas en cada contrato. Los importes físicos se manejan como decimales y USD se define en configuración; no se añade selector de divisa. Las comparaciones de identidad usan normalización y locale ICU. La portabilidad tiene límites concretos: la imagen se comprobó en Linux/amd64 sobre Docker Desktop, no en toda arquitectura o proveedor.

## Seguridad y mantenibilidad

Un token o cookie debe tener vigencia y permisos, no solo existir. La sesión dura treinta minutos sin renovarse por el polling; el límite de intentos se comparte mediante PostgreSQL. Se mantuvo CSRF. El permiso de QR HTTP local es explícito y se prueba que no permite destinos externos inseguros.

La separación entre requirements.txt y requirements-deploy.txt evita instalar el servidor de despliegue en todos los flujos de desarrollo. Las imágenes se fijan por digest y los archivos mantienen versiones exactas. Los cambios futuros de versión requieren reconstruir, revisar avisos de seguridad y volver a ejecutar los controles pertinentes; el digest fija una revisión, no garantiza que nunca aparezcan vulnerabilidades.

## Fuentes primarias

- HTTP: https://www.rfc-editor.org/rfc/rfc9110.html
- JSON: https://www.rfc-editor.org/rfc/rfc8259.html
- OpenAPI: https://spec.openapis.org/oas/v3.1.0
- WSGI: https://peps.python.org/pep-3333/
- Compose y arranque: https://docs.docker.com/compose/how-tos/startup-order/
- Secretos de Compose: https://docs.docker.com/compose/how-tos/use-secrets/
- Django: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Gunicorn: https://gunicorn.org/run/
- WhiteNoise: https://whitenoise.readthedocs.io/en/stable/django.html
- OWASP: https://owasp.org/API-Security/editions/2023/en/0x11-t10/
