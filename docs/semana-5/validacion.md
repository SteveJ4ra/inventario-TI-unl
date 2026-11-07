# Validación del incremento de semana 5

Base integrada: develop 435b0e0, después de los PR #27, #28 y #29. Rama local: feature/semana-5-integracion. Proyecto de prueba: inventario-ti-u1-validacion. Fecha académica: 06/11/2026. Los valores proceden de ejecuciones reales; evidencia estructurada en evidencia-validacion.json.

| Verificación | Resultado observado | Alcance |
| --- | --- | --- |
| Construcción y dependencias | Imagen construida; pip check sin incompatibilidades | Python 3.13.18, Django 5.2.18, Gunicorn 26.2.0, WhiteNoise 6.12.0 |
| Suite del backend en Docker | 333 pruebas correctas en 28,139 segundos | 303 de inventory y 30 contractuales; PostgreSQL testdb separado |
| Suites aisladas | 21 de políticas y 16 de importación, correctas | Dominio puro, sin confundirlas con las pruebas de PostgreSQL |
| HTTP sobre Gunicorn | 30 respuestas comprobadas | Documentación, esquema, JS, CSS, sesión/CSRF, alta/consulta, entrega/devolución, historial, QR, errores y bloqueo |
| Rol operativo | inventario_app: no superusuario, no CREATEDB, no CREATEROLE | Consulta directa del rol utilizado por la aplicación |
| Usuario del contenedor | UID 10001 | Proceso de demostración ejecutado sin root |
| Migraciones | No changes detected | Base de prueba; no se alteró la base operativa del usuario |
| Persistencia | Dos activos antes y dos después | down sin --volumes y nuevo up; volumen conservado |
| Control de despliegue Django | Cuatro advertencias: W004, W008, W012 y W016 | Corresponden a HTTP local; no se silencian ni se declara TLS público |

## Hallazgos de integración corregidos

| Problema observado | Corrección | Evidencia posterior |
| --- | --- | --- |
| La contraseña creada con CRLF en Windows no coincidía con la leída por Linux | Generar secretos con LF explícito; normalizar únicamente los archivos de la prueba recién creada | Nueva inicialización y autenticación PostgreSQL correctas |
| collectstatic no podía crear su directorio con UID 10001 | Crear staticfiles con propietario limitado en la imagen | CSS servido con 200 y proceso sin root |
| Dos pruebas históricas no encontraban la plantilla SDD de migración | Conservar la estructura backend/specs e incluir solo esa plantilla en el contexto | Suite completa correcta; sin omitir esas pruebas |
| El QR local devolvía 500 con DEBUG=false por exigir HTTPS para toda URL | Permiso de HTTP explícito y limitado a loopback; validar URL al inicializar | SVG 200 y dos regresiones de URL local/externa |

## Recorrido HTTP demostrado

Se obtiene CSRF, inicia sesión un gestor ficticio, se registra un custodio, se rechaza un alta inválida y se crea un activo con factura/facultad de prueba. Se consulta la ficha, se rechaza devolverlo sin entrega (409), se entrega y devuelve correctamente, y se comprueba que queda Disponible/sin custodio con dos movimientos. El QR devuelve SVG. Se comprueba el vencimiento guardado de treinta minutos y se provoca la caducidad de la sesión de prueba para obtener 403; cinco fallos de acceso y el siguiente intento correcto producen 429 con Retry-After. Los datos no se publican como institucionales; la cuenta temporal se desactiva al finalizar.

## Límites interpretados

No se desplegó una URL pública, TLS, frontend React, correo institucional ni una infraestructura universitaria. El QR conserva el enlace al frontend configurado y la descarga SVG se comprobó; la navegación final requiere ese frontend. Las pruebas no equivalen a pentesting externo, carga intensiva o certificación de seguridad. Los importes físicos cero/negativos y la fecha documental de una donación tienen rechazos explícitos según el contrato actual; no se inventa soporte para esos casos. Los valores y fechas de licencias siguen sus reglas propias, incluyendo cero puestos y fecha final opcional.

La versión previa del API bajo /api/ conserva sus formatos; /api/v1/ y OpenAPI cubren el recorrido base y el sobre JSON definido, no todos los módulos. El catálogo-api.md enumera las rutas reales y remite a los contratos por módulo. No se aplicó una migración a datos históricos reales ni se sustituyó su facultad con información ficticia.

## Reproducción

Seguir deploy/README.md. Los informes documentan comprobaciones locales del incremento; los enlaces de PR de semana 5 se incorporan cuando existan, sin confundirlos con los merges reales de semanas anteriores.
