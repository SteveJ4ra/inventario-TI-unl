# ADR-0401 · Sesiones acotadas y control compartido de intentos

Estado: Propuesto para aceptación del equipo. Proyecto: Inventario TI. Base: develop 5ac5cb9.

## Contexto y criterios

La aplicación usa Django, DRF y PostgreSQL y debe conservar los flujos y permisos existentes. SEC-01 demuestra intentos repetidos sin límite; la observación docente pide volver a solicitar credenciales tras un plazo. Se priorizan consistencia entre procesos, privacidad, verificabilidad y alcance viable.

## Alternativas

| Criterio | Sesión y contador PostgreSQL | Tokens bearer y límites en memoria |
| --- | --- | --- |
| Integración | Conserva autenticación y CSRF existentes | Requiere migrar clientes, emisión y revocación |
| Expiración | Fecha absoluta comprobada en servidor | El formato del token no garantiza una política adecuada |
| Concurrencia | Bloqueo de fila por cuenta e IP | Los contadores en memoria por proceso no coordinan varios procesos |
| Costo | Reutiliza la base y agrega una tabla operativa | Menos escrituras por contador, pero debe resolverse la coordinación |

Un almacén externo con operaciones atómicas es otra posibilidad, con infraestructura adicional. La documentación de DRF advierte que su throttling no debe considerarse por sí solo una garantía de seguridad contra fuerza bruta.

## Decisión y justificación

Mantener el identificador de sesión en cookie HttpOnly y CSRF. Fijar un vencimiento absoluto de treinta minutos desde el login; es una política conservadora del proyecto, no una duración impuesta por OWASP. La sensibilidad de entregas, bajas y datos de custodios justifica volver a autenticar y evitar que el refresco automático conserve el acceso indefinidamente. Aplicar cinco fallos por cuenta e IP en quince minutos mediante PostgreSQL y responder 429 con Retry-After al alcanzar el bloqueo.

## Consecuencias, riesgos y mitigaciones

Se conservan clientes y permisos, con controles reproducibles. La contrapartida es reautenticación periódica incluso durante uso continuo y consultas adicionales a la base. Tras cinco fallos también se rechaza temporalmente una contraseña correcta. El límite no resuelve ataques distribuidos; un proxy requiere confianza de IP explícita. La operación debe limpiar contadores expirados y caducar sesiones anteriores al desplegar la política.

## Trazabilidad y verificación

RNF-01 y RNF-05; AM-01, AM-05 y AM-08; SEC-01, SEC-02 y SEC-05; CS-01–CS-07. Código: auth_views.py, login_security.py, privacy.py y configuración Django. Pruebas: LoginLimitTests y ConcurrentLoginLimitTests. La propuesta se publicará con el PR correspondiente cuando se autorice.

## Referencias

- https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- https://docs.djangoproject.com/en/5.2/topics/http/sessions/
- https://www.django-rest-framework.org/api-guide/throttling/
