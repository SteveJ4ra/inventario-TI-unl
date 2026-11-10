# Evidencia y operación de seguridad

## Resultados ejecutados

| Revisión | Resultado observado | Alcance |
| --- | --- | --- |
| Antes del control de acceso | El sexto fallo recibió 400, no 429; una prueba falló | Reproducción en PostgreSQL temporal sobre la base de semana 3 |
| Antes de la política de caché | /api/auth/me/ no incluyó Cache-Control; la prueba no-store falló | Se comprobó ausencia de directiva, no almacenamiento efectivo |
| Pruebas específicas de seguridad | 12 aprobadas | Bloqueo, expiración, concurrencia, caché, errores, entrada inválida y sesión de treinta minutos |
| Suite completa tras correcciones | 297 aprobadas | Backend y recorrido HTTP con PostgreSQL temporal |
| Migraciones y modelos | No changes detected | makemigrations --check --dry-run en entorno temporal |
| OpenAPI | Válido y exportado | Se añadió 429 a login y se documentaron límite y sesión |

En una ejecución intermedia falló una prueba antigua que fijaba 0007 como última migración. Se corrigió para exigir una única rama de migraciones que incluya esa migración y se mantuvo la comparación entre estado y modelos. La suite completa posterior pasó. Las pruebas usan credenciales ficticias; algunas sustituyen el hasher por uno rápido exclusivamente en el entorno de prueba. La configuración de la aplicación conserva los hashers normales de Django.

Para sesión se comparó la fecha absoluta guardada con el reloj del servidor y se forzó una sesión caducada en la base temporal para comprobar su rechazo. Esa prueba verifica la transición sin tener que mantener una ejecución esperando treinta minutos.

La inspección actual de archivos y patrones de exclusión no encontró archivos .env locales versionados ni marcadores de claves privadas. Su alcance no demuestra ausencia absoluta de secretos en todo el historial y no incluye una auditoría exhaustiva de dependencias.

## Preparar y probar

Desde la raíz del repositorio y con el entorno Python preparado según backend/README.md:

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory --verbosity 1
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py --manage makemigrations --check --dry-run
```

Estas pruebas usan una base temporal; no modifican la base operativa del usuario.

## Aplicar al integrar el cambio

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py migrate
& .\backend\.venv\Scripts\python.exe backend/manage.py expire_legacy_sessions
```

El segundo comando caduca sesiones anteriores sin una fecha absoluta válida dentro del plazo configurado para que vuelvan a autenticarse. No elimina movimientos, custodios ni activos. Después, cada login dura treinta minutos desde su creación; los refrescos no prolongan el plazo. Tras vencer, una petición protegida se rechaza y el cliente debe volver a solicitar credenciales. Las pantallas que no estén haciendo peticiones pueden conservar su representación hasta que consulten de nuevo; no disponen de acceso autorizado al servidor después del vencimiento.

Para mantenimiento operativo autorizado:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py cleanup_login_attempts
& .\backend\.venv\Scripts\python.exe backend/manage.py clearsessions
```

No se programa automáticamente una tarea externa en esta entrega. La frecuencia operativa y la configuración de producción se documentarán al preparar el despliegue. La aplicación local no se presenta como un servicio público con TLS.


## Ajustes de la revisión final

Se hizo atómica la obtención o creación del contador bajo bloqueo para evitar una ventana frente a su limpieza. El comando de transición se endureció para fechas malformadas, sin zona horaria o excesivamente lejanas; una prueba nueva verificó estos casos y se conservó la prueba que preserva sesiones nuevas válidas. El contrato incorporó las restricciones del identificador de cuenta.
