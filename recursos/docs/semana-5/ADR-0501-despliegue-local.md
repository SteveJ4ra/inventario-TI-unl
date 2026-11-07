# ADR-0501 - Despliegue local con contenedores

Estado: implementado y comprobado localmente. Base integrada: develop 435b0e0. Alcance autorizado: backend y PostgreSQL en Docker Compose, con evidencia reproducible; no hay publicación en un servidor externo.

## Contexto

La semana 5 exige integrar, contenerizar, desplegar y explicar interoperabilidad y mantenibilidad. Los módulos 002-008 y los controles de semana 4 ya están integrados. La aplicación tiene restricciones PostgreSQL/ICU, sesiones y CSRF; una demostración con runserver no verifica un servidor WSGI ni el aislamiento del rol de base.

## Alternativas y decisión

| Alternativa | Ventaja | Coste o límite | Decisión |
| --- | --- | --- | --- |
| Python y PostgreSQL instalados directamente | Menos capas y útil para desarrollar | Depende de versiones, locale y configuración de cada equipo | Conservar como opción documentada |
| Compose: Gunicorn, PostgreSQL y servicio de inicialización | Entorno definido, orden de arranque, rol limitado y prueba repetible | Requiere Docker y recursos locales; no provee TLS por sí solo | Elegida para semana 5 |
| Plataforma o servidor público | Acceso externo | Requiere cuenta, infraestructura, dominio, TLS y operación | Fuera del despliegue confirmado |

Usar Python 3.13 y PostgreSQL 17 oficiales fijados por digest. Gunicorn 26.2.0 ejecuta WSGI con dos workers sin root; WhiteNoise 6.12.0 sirve estáticos recolectados. Las dependencias extra se limitan al despliegue y se separan de requirements.txt. No se cambia el dominio ni los contratos existentes.

## Consistencia, seguridad y portabilidad

- db se comprueba mediante healthcheck; initialize migra una vez antes del servidor. El volumen es persistente.
- La base de pruebas tiene servidor y rol propios; la aplicación no puede crear bases ni roles.
- Los secretos se generan fuera de Git, con LF y sin valores en la imagen. Compose los monta como archivos.
- El puerto se liga a loopback; HTTP local se distingue de una publicación segura con TLS.
- La excepción QR de HTTP requiere permiso explícito y hostname de loopback; un destino externo inseguro sigue rechazándose.
- El contenedor conserva backend/ y la plantilla SDD que utilizan las pruebas históricas de migración. El contexto excluye entornos virtuales, resultados y secretos.

## Verificación y consecuencias

333 pruebas en Docker, 30 comprobaciones HTTP y persistencia tras down/up sin borrar volumen. El perfil local conserva las cuatro advertencias HTTPS de check --deploy, que se documentan en vez de ocultarse. Las pruebas no certifican producción pública ni acceso a infraestructura universitaria. Se mantienen los mecanismos de sesión de treinta minutos y cinco fallos por cuenta/IP de semana 4.

Referencias: https://docs.docker.com/compose/how-tos/startup-order/ ; https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ ; https://gunicorn.org/run/ ; https://whitenoise.readthedocs.io/en/stable/django.html .
