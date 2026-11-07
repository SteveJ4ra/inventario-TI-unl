# Hallazgos y priorización de seguridad

## Método

Probabilidad e impacto se valoran de 1 a 3. Se aplica la matriz de AA 4: producto 1–2 Bajo, 3–4 Medio, 6 Alto y 9 Crítico. La puntuación es una estimación justificada del escenario, no una medición de ataques reales. La prueba de un control ausente no demuestra que una cuenta haya sido comprometida o que el navegador haya almacenado datos.

## SEC-01 · Ausencia de limitación de intentos de acceso

| Elemento | Evidencia o valoración |
| --- | --- |
| Estado | Hallazgo comprobado y corregido en el trabajo local de semana 4 |
| Amenaza y activo | AM-01; cuentas y disponibilidad |
| Causa | El acceso anterior ejecutaba autenticación sin un contador de fallos |
| Evidencia inicial | En develop 5ac5cb9, la prueba del sexto fallo esperaba 429 y recibió 400; no había rechazo por frecuencia |
| Riesgo inicial | P=2 e I=3: 6, Alto. Un cliente que puede acceder al servicio puede repetir intentos; comprometer una cuenta afectaría operaciones sensibles, pero no se demostró compromiso |
| Prioridad | Corregir antes de cerrar el incremento |
| Control añadido | Cinco fallos en quince minutos por cuenta e IP, compartidos entre versiones y procesos mediante PostgreSQL; respuesta 429 con Retry-After |
| Verificación | Bloqueo, expiración, éxito que reinicia contador, cabecera de IP no confiable e intentos simultáneos en test_login_security.py |
| Riesgo residual | No detiene un ataque distribuido con muchas combinaciones; AM-08 requiere controles operativos adicionales antes de una exposición pública |

El contador utiliza una clave HMAC y no almacena cuenta o IP en texto. Solo se utiliza REMOTE_ADDR; no se confía en X-Forwarded-For del cliente. Un proxy requiere una configuración de confianza explícita antes de modificar esta regla. La ventana empieza con el primer fallo de la serie; tras cinco fallos también se rechaza una contraseña correcta hasta finalizar el plazo.

## SEC-02 · Respuestas sensibles sin directiva no-store

| Elemento | Evidencia o valoración |
| --- | --- |
| Estado | Ausencia de directiva comprobada y corregida; no se midió almacenamiento efectivo en un navegador |
| Amenaza y activo | AM-05; datos de sesión y de inventario |
| Evidencia inicial | La prueba sobre /api/auth/me/ recibió una respuesta sin Cache-Control; la aserción no-store falló |
| Riesgo inicial | P=1 e I=3: 3, Medio. Requiere condiciones de caché o dispositivo compartido; expondría información protegida |
| Control añadido | Middleware para /api/ que impide almacenamiento y distingue respuestas por cookie; conserva endpoints que ya establecían no-store |
| Verificación | test_api_responses_prevent_shared_and_browser_caching, en ambas versiones |
| Riesgo residual | Las directivas dependen del comportamiento del cliente; no sustituyen cerrar sesión ni proteger el dispositivo |

## Riesgos potenciales y controles comprobados

### SEC-05 · Política corta de sesión no definida

La configuración anterior no acortaba la duración predeterminada de Django. No se comprobó una sesión literalmente infinita; el hallazgo consiste en que no había una política breve acorde con la observación docente. Se adoptó una duración absoluta de treinta minutos, guardada como fecha en la sesión, sin renovación por consultas automáticas. P=2 e I=2: 4 Medio, porque una sesión abierta en un equipo accesible podría reutilizarse. Se verifica el plazo, la ausencia de extensión al consultar y el rechazo tras caducar la sesión en servidor. La transición requiere ejecutar `expire_legacy_sessions` al desplegar.

| ID | Clasificación | Riesgo y fundamento | Valoración y tratamiento |
| --- | --- | --- | --- |
| SEC-03 | Riesgo potencial de despliegue | El entorno local usa HTTP y no configura cookies Secure. Es compatible con localhost; no se declara un despliegue público seguro | P=1, I=3: 3 Medio para el alcance local. Exigir TLS y configuración segura antes de publicar |
| SEC-04 | Riesgo potencial residual | Muchas cuentas/IP distintas pueden evitar el límite por combinación y hacer crecer contadores | P=2, I=2: 4 Medio. Limpiar contadores expirados y definir límites de infraestructura si se expone el servicio; no se realizaron pruebas de carga |
| CTRL-01 | Control existente | Permisos por rol y por solicitud asignada | Pruebas existentes de permisos y de integración; no se identificó un bypass en los escenarios examinados |
| CTRL-02 | Control existente | Validaciones estrictas, CSRF, revisión concurrente y auditoría | Pruebas de permisos, custodia, rectificación y concurrencia; no se asume cobertura de toda entrada imaginable |

## Límites

No se realizaron pruebas de penetración externas, auditoría exhaustiva de dependencias, cargas intensivas, evaluación de TLS de producción o revisión completa del historial Git. La inspección de archivos versionados y configuración distingue fixtures de prueba de secretos reales; sus valores no deben copiarse a los informes. Las conclusiones se limitan al código, configuración y pruebas examinados.
