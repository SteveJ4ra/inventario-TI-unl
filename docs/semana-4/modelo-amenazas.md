# Modelo de amenazas del Inventario TI

## Alcance y límites de confianza

Base: develop 5ac5cb9. El análisis cubre el acceso por sesión y el flujo de registro, consulta, entrega y devolución de activos. Se revisan también como contexto los controles existentes de revisores y operadores; no se amplían sus permisos. Las pruebas se ejecutan en el entorno local del proyecto, con datos ficticios y PostgreSQL temporal. No se prueban sistemas de la universidad ni servicios ajenos.

El navegador es una entrada no confiable. Las cookies y el token CSRF atraviesan la frontera hacia Django/DRF. Los permisos y servicios verifican identidad, acción y reglas antes de escribir en PostgreSQL. El rol de gestor tiene alcance sobre todo el inventario por decisión del proyecto: consultar activos registrados por otro gestor no constituye una infracción por sí mismo. La autorización por objeto es especialmente relevante para el revisor de una solicitud de baja.

## Activos

| ID | Activo | Acceso esperado | Impacto de exposición, alteración o pérdida |
| --- | --- | --- | --- |
| A-01 | Cuentas, contraseñas derivadas y sesiones | Titular y componentes de autenticación | Suplantación y acceso a operaciones de inventario |
| A-02 | Datos de activos y adquisiciones | Gestores; acceso técnico limitado según operación | Pérdida de integridad, trazabilidad y control institucional |
| A-03 | Nombre, correo y dependencia de custodios | Gestores autorizados | Exposición de datos personales |
| A-04 | Movimientos, autores y antecedentes | Gestores y componentes autorizados | Alteración o pérdida de evidencia |
| A-05 | Solicitudes y decisiones de baja | Gestores y revisor asignado según contrato | Baja no autorizada o encubrimiento de movimientos |
| A-06 | Configuración y secreto de la aplicación | Operación técnica, fuera del repositorio | Compromiso de sesiones, base o servicio |
| A-07 | Disponibilidad y contadores de acceso | Servicio de autenticación; limpieza local autorizada | Consumo de recursos o bloqueo temporal de acceso |

## Matriz de actores y permisos

| Operación | Anónimo | Gestor | Operador | Revisor |
| --- | --- | --- | --- | --- |
| Obtener CSRF e intentar iniciar sesión | Sí | Sí | Sí | Sí |
| Consultar documentación de API | Sí, sin datos protegidos | Sí | Sí | Sí |
| Consultar y gestionar inventario | No | Sí, ámbito global acordado | No, salvo operaciones explícitas de facultad | No |
| Administrar facultades y cuentas revisoras | No | No | Sí | No |
| Resolver solicitud de baja | No | No por ser gestor | No por ser operador | Solo solicitud asignada y condiciones de independencia |
| Cambiar contraseña inicial revisora | No | Según su cuenta | Según su cuenta | Sí; el cambio inicial es obligatorio |

El custodio es una persona sin cuenta de acceso. Un superusuario Django sin el grupo correspondiente no adquiere automáticamente permisos de inventario.

## Superficies de ataque

Rutas de autenticación, identificadores de activos y solicitudes, query parameters, cuerpos JSON, cabeceras, cookies, CSV existentes y la página de documentación. Se revisan también configuración y archivos versionados. El CDN de Swagger es una dependencia externa de la documentación; la tabla protegida y el esquema se sirven localmente.

## Amenazas y controles

| ID | Escenario y categoría STRIDE | Activo | Control y evidencia |
| --- | --- | --- | --- |
| AM-01 | Suplantar una cuenta mediante intentos repetidos | A-01, A-07 | Límite de cinco fallos en quince minutos por cuenta e IP; test_login_security.py |
| AM-02 | Forzar una escritura con sesión desde otro origen | A-02, A-04 | CSRF y permisos en servidor; test_permissions.py y test_api_v1.py |
| AM-03 | Alterar custodia, autor o revisión de forma arbitraria | A-02, A-04 | Serializadores estrictos y servicios transaccionales; test_custody.py |
| AM-04 | Consultar o decidir una solicitud asignada a otro revisor | A-05 | Filtro y permiso por objeto; test_retirement_permissions.py y test_retirement_integration.py |
| AM-05 | Conservar datos sensibles en cachés no previstas | A-01, A-03 | Política no-store en respuestas API; test_login_security.py |
| AM-06 | Revelar detalles internos a través de errores | A-06 | Errores JSON genéricos en v1 y DEBUG desactivado por defecto; test_login_security.py |
| AM-07 | Ejecutar contenido de un nombre como HTML en documentación | A-01, A-03 | Uso de textContent; docs-live.test.js |
| AM-08 | Consumir recursos con muchas combinaciones de cuenta e IP | A-07 | Límite por combinación y limpieza de contadores expirados; no sustituye un límite global ni pruebas de carga |

## Autenticación y autorización

La autenticación determina la identidad mediante credenciales y sesión Django. La autorización se comprueba mediante grupos, estado de cuenta y reglas por recurso u objeto. Un token CSRF evita una clase de solicitudes forjadas; no sustituye la sesión ni los permisos. A partir de la observación docente se adoptó un vencimiento absoluto de treinta minutos desde el acceso; las consultas automáticas no lo amplían. La cookie contiene el identificador de sesión, no las credenciales. Al vencer, el servidor rechaza el acceso y una nueva autenticación vuelve a exigir usuario y contraseña.

## Fuentes

- OWASP API Security Top 10 2023: https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- DRF Throttling: https://www.django-rest-framework.org/api-guide/throttling/
