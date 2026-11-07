# Despliegue local reproducible del backend

Desde la raíz del repositorio; requiere Docker Desktop con motor Linux (o Docker Engine y Compose en Linux) y Python local para generar secretos. Se comprobó Docker 29.5.3 y Compose 5.1.4. Las imágenes base se fijaron por digest; las dependencias de aplicación y despliegue tienen versión exacta. El despliegue sirve la API y su documentación; React se ejecuta por separado.

## Preparar y arrancar

```powershell
python deploy/prepare_secrets.py
docker compose config --quiet
docker compose build web
docker compose up -d --wait --no-build web
docker compose ps --all
```

En Linux, usar python3 si corresponde. El generador prepara cuatro archivos en deploy/.secrets, no imprime sus valores y nunca reemplaza un archivo existente. Escribe LF explícitamente para no alterar contraseñas entre Windows y Linux. Los archivos están ignorados por Git y por el contexto de construcción. Los secretos de Compose son archivos montados, no un almacén cifrado: proteger también la cuenta y los archivos del equipo anfitrión.

La URL es http://localhost:8005/api/docs/; esquema: http://localhost:8005/api/openapi.json. Para otro puerto en PowerShell, definir $env:COMPOSE_HTTP_PORT="8010" antes de los comandos; en Linux, export COMPOSE_HTTP_PORT=8010. El servidor está publicado exclusivamente en 127.0.0.1. PostgreSQL no publica puerto al anfitrión.

El QR utiliza PUBLIC_APP_URL (por defecto http://127.0.0.1:5173, correspondiente al frontend existente). El backend descarga el SVG y resuelve el código, pero el recorrido de navegación requiere que ese frontend esté activo por separado. El permiso QR_ALLOW_LOCAL_HTTP de este Compose admite HTTP solo para localhost, 127.0.0.1 o ::1. Los destinos externos siguen exigiendo HTTPS con DEBUG=false; no se obtiene el destino de la cabecera Host.

## Base de datos, orden de inicio y cuentas

El servicio db crea un administrador de inicialización y un rol inventario_app sin SUPERUSER, CREATEDB ni CREATEROLE. La aplicación usa solo el segundo, propietario de su base. El locale ICU preserva las comparaciones Unicode requeridas por el dominio. El volumen pgdata conserva la información tras recrear contenedores.

Compose espera db saludable, ejecuta initialize (check, migraciones y caducidad de sesiones anteriores) y solo después inicia web. Gunicorn ejecuta dos workers como UID/GID 10001; collectstatic usa un directorio autorizado para ese usuario y WhiteNoise sirve los estáticos. Las migraciones no se ejecutan desde cada worker.

No hay gestor ni contraseña predeterminados. Crear cuentas propias de forma interactiva:

```powershell
docker compose exec web python manage.py create_gestor
docker compose exec web python manage.py create_operator
```

Las contraseñas se solicitan sin incorporarlas a Git. Para desactivar un gestor autorizado: docker compose exec web python manage.py deactivate_gestor NOMBRE_EXACTO. No crear una cuenta si ya existe una apropiada. Las cuentas revisoras se administran mediante las operaciones del operador descritas en el contrato 005.

Las instalaciones con datos históricos requieren respaldo y los diagnósticos de adquisición documentados en specs/003-fichas-adquisiciones/migration-notes/. No asignar facultades ficticias a equipos reales para forzar una migración; el flujo demostrado usa una base nueva y datos de prueba.

## Pruebas aisladas y demostración

```powershell
docker compose --profile test run --rm tests
docker compose --profile test run --rm tests makemigrations --check --dry-run
docker compose exec web python manage.py check --deploy
```

El comando de pruebas incluye inventory y contract_tests.

Para las suites aisladas:

```powershell
docker compose --profile test run --rm --entrypoint python tests -m unittest discover -s inventory/isolated_tests/approval -v
docker compose --profile test run --rm --entrypoint python tests -m unittest discover -s inventory/isolated_tests/imports -v
```

El perfil test usa testdb separado, sin puerto publicado y con datos efímeros en tmpfs. El administrador de ese servidor puede crear la base temporal de Django; no se concede ese privilegio al usuario operativo. El runner no usa la base db ni backend/.env.

Para demostrar el ciclo HTTP se puede ejecutar:

```powershell
docker compose exec -T -e INVENTORY_ALLOW_DEMO_DATA=1 web python deploy/smoke.py
```

Este último comando crea registros claramente ficticios en la base de demostración: un gestor, facultad, factura, custodio y activo. Comprueba 30 respuestas HTTP, sesión/CSRF, alta inválida, consulta, entrega, devolución, historial, QR, expiración y bloqueo. La cuenta temporal se desactiva al terminar y los antecedentes se conservan. No usarlo sobre datos operativos; exige la confirmación y la combinación de base/rol/servicio de este despliegue.

## Operación y límites

```powershell
docker compose logs --tail 80 web initialize
docker compose exec web python manage.py cleanup_login_attempts
docker compose exec web python manage.py clearsessions
docker compose down
```

El último comando detiene servicios y conserva el volumen. No añadir --volumes cuando se quiera conservar información. No regenerar secretos existentes como una forma de recuperar acceso: una rotación requiere actualizar de manera coordinada la base y la aplicación.

Ejemplo de respaldo manual del volumen de demostración, preservando el formato binario también en Windows PowerShell:

```powershell
docker compose exec -T db pg_dump -U inventario_admin -Fc -f /tmp/inventario.dump inventario_ti
docker compose cp db:/tmp/inventario.dump ./inventario.dump
```

El respaldo contiene datos y debe guardarse fuera del repositorio, con permisos apropiados. La recuperación exige elegir una base destino expresamente; no se ejecuta automáticamente ni se ha certificado restauración de datos institucionales.

El perfil HTTP local produce W004, W008, W012 y W016 de check --deploy porque no habilita TLS/HSTS/cookies Secure. No se silencian ni se presenta este entorno como producción pública. Para un despliegue público se necesita infraestructura HTTPS real, hosts/orígenes correctos, permisos/retención de respaldos y una revisión operativa. La opción DJANGO_HTTPS=true del perfil activa redirección, cookies Secure y HSTS; no configura certificados ni un proxy de confianza. Swagger necesita conexión a su CDN; el esquema JSON y live.js son locales.

Resultados y límites: docs/semana-5/validacion.md. No publicar deploy/.secrets, respaldos, archivos .env ni la carpeta de resultados locales.
