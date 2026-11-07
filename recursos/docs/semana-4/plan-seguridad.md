# Plan y criterios del incremento de seguridad

## Decisiones confirmadas

Mantener sesión Django y CSRF. Aplicar el límite aprobado de cinco fallos en quince minutos por cuenta e IP, compartido por /api/ y /api/v1/. Mantener los permisos de inventario global de los gestores y los permisos existentes de operadores y revisores. No incorporar un proveedor externo de identidad ni un nuevo rol.

El docente observó que el acceso debía volver a pedir credenciales tras un tiempo determinado. Se eligió un vencimiento absoluto de treinta minutos desde el login, ajustado a operaciones sensibles de inventario y a sesiones de demostración. Es un límite fijo, no un plazo de inactividad: el uso continuo y las consultas del panel tampoco lo renuevan. Se mantiene un identificador de sesión opaco en cookie HttpOnly y la validación de la sesión en servidor; el formato del identificador no sustituye la expiración.

## Criterios de aceptación

- CS-01: cinco fallos de acceso se procesan; el sexto se rechaza con 429 y Retry-After antes de autenticar. El límite no puede evitarse alternando versiones de la API.
- CS-02: al terminar la ventana se admite un intento nuevo; un acceso correcto anterior al bloqueo reinicia el contador.
- CS-03: solicitudes simultáneas comparten el contador y no permiten más fallos que los acordados. No se confía en X-Forwarded-For sin una infraestructura de confianza configurada.
- CS-04: respuestas sensibles de ambas API incluyen no-store y varían por cookie. Se mantienen las directivas de endpoints que ya impedían almacenamiento.
- CS-05: los errores internos de v1 mantienen el sobre JSON y omiten detalles internos del fallo.
- CS-06: las pruebas de autorización, validaciones y transacciones del proyecto siguen pasando; las pruebas fallidas previas y las correcciones se documentan sin inventar resultados.
- CS-07: cada nuevo login vence a los treinta minutos; las consultas de datos y CSRF no extienden ese instante. Una sesión vencida no puede acceder a datos protegidos. Al desplegar, se caducan las sesiones anteriores sin vencimiento absoluto mediante el comando operativo correspondiente.

## Implementación y operación

La migración 0008_login_attempt incorpora el contador. Cada clave agrupa cuenta y REMOTE_ADDR mediante HMAC; la obtención o creación bajo bloqueo de fila serializa intentos de la misma combinación y evita un hueco frente a la limpieza concurrente. Es un contador operativo, no el historial de activos. `python backend/manage.py cleanup_login_attempts` elimina únicamente contadores cuya ventana ya expiró; se recomienda ejecutarlo periódicamente desde la operación autorizada. Cambiar DJANGO_SECRET_KEY invalida las claves de agrupación anteriores y requiere una rotación operativa planificada.

Después de aplicar migraciones y antes de dar por desplegada la política se ejecuta `python backend/manage.py expire_legacy_sessions`. Caduca sesiones sin una fecha absoluta válida y acotada al plazo configurado; obliga a autenticarse otra vez. Conserva las sesiones nuevas con su fecha de vencimiento. Este comando no borra movimientos ni registros de inventario.

## Trazabilidad

| Amenaza / hallazgo | Requisito relacionado | Control | Prueba |
| --- | --- | --- | --- |
| AM-01 / SEC-01 | RNF-01; CS-01–CS-03 | login_security.py y contador PostgreSQL | LoginLimitTests y ConcurrentLoginLimitTests |
| AM-05 / SEC-02 | RNF-01; CS-04 | privacy.py | test_api_responses_prevent_shared_and_browser_caching |
| AM-06 | RNF-01 y RNF-05; CS-05 | Manejador de errores y adaptador v1 | test_internal_error_has_generic_json_without_sensitive_detail |
| SEC-05 y observación docente | RNF-01; CS-07 | Vencimiento absoluto y caducidad de sesiones anteriores | Pruebas de duración, consultas sin extensión y transición operativa |
| AM-02 y AM-03 | 002/FR-010, FR-012–FR-014; CS-06 | CSRF, permisos, servicios y restricciones | test_permissions.py, test_custody.py y test_concurrency.py |

## Tareas

- [x] Analizar consignas y fuentes OWASP.
- [x] Reproducir la ausencia del límite y de la directiva de caché.
- [x] Implementar controles y pruebas específicas.
- [x] Ejecutar suite completa, comprobar migraciones y actualizar OpenAPI.
- [x] Preparar informes AA, ACD y APE y paquetes de publicación.
- [ ] Registrar revisión cruzada efectiva y enlaces de aportes cuando existan.
