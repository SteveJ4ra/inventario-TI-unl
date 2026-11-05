# Backend · Inventario TI

Python 3.13, Django 5.2.18, Django REST Framework 3.18.2 y PostgreSQL 17. DRF se actualizó por seguridad con autorización de Anderson; las demás versiones se conservaron. Versiones exactas: requirements.txt. Implementa activos, custodios, operaciones transaccionales e historial; contratos: [API](../specs/002-registro-consulta-activos/contracts/api.md).

## Preparar una instalación nueva

PowerShell desde la raíz del repositorio:

```powershell
python -m venv backend/.venv
& .\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

En Linux: `python3.13 -m venv backend/.venv`, después `backend/.venv/bin/python -m pip install -r backend/requirements.txt`.

PostgreSQL debe estar activo. Si todavía no existen rol/base, el administrador local puede crearlos desde psql:

```sql
CREATE ROLE inventario_app WITH LOGIN;
```

Asignar contraseña de forma interactiva con `\password inventario_app`. Crear la base propia:

```sql
CREATE DATABASE inventario_ti OWNER inventario_app ENCODING 'UTF8'
  LOCALE_PROVIDER icu ICU_LOCALE 'und' TEMPLATE template0;
```

Se requiere comparación de mayúsculas Unicode para textos con tildes. La base local existente usa Spanish_Ecuador.1252 y fue comprobada; no es necesario recrearla. Las instalaciones nuevas pueden utilizar ICU como en el ejemplo. No crear de nuevo roles/bases que ya existen y no conceder CREATEDB a inventario_app para ejecutar tests.

Solo si backend/.env no existe, copiar backend/.env.example y completar localmente DJANGO_SECRET_KEY, DJANGO_DEBUG y DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT. No publicar ese archivo. Generar la clave desde Python con django.core.management.utils.get_random_secret_key y guardarla localmente; no usar una clave fija compartida.

## Migrar y preparar gestores

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py check
& .\backend\.venv\Scripts\python.exe backend/manage.py migrate
& .\backend\.venv\Scripts\python.exe backend/manage.py create_gestor
```

create_gestor pide usuario nuevo y contraseña dos veces; valida ambos y añade el grupo Gestores. No cambia contraseñas de cuentas existentes ni crea superusuarios. Un usuario autenticado sin grupo Gestores, incluso superusuario, no puede operar en el inventario. La autorización institucional de personas reales corresponde al equipo responsable; no hay registro público.

Las migraciones crean las tablas y restricciones propias del inventario, la secuencia de código TI y el trigger que impide reescribir/borrar movimientos. No se registran los modelos de inventario como admin editable. La rectificación añade un evento vinculado y restaura la ficha; no modifica el original.

## Ejecutar

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

La pantalla se ejecuta aparte en frontend, normalmente http://127.0.0.1:5173/. API bajo http://127.0.0.1:8000/api/. La raíz del backend puede responder 404; no es una falla de la aplicación. Detener con Ctrl+C.

Sesiones Django y CSRF en escrituras, incluido login. Orígenes de desarrollo por defecto: http://127.0.0.1:5173 y http://localhost:5173. Para otro puerto, definir DJANGO_CSRF_TRUSTED_ORIGINS con lista separada por comas y configurar el proxy del frontend; no usar comodines. Fechas almacenadas con zona horaria; la web presenta America/Guayaquil.

## Probar sin alterar la base local

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py
& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
& .\backend\.venv\Scripts\python.exe -m pip check
```

El runner busca initdb/pg_ctl en PostgreSQL 17 de Windows o PATH; PG_BIN permite indicar otra carpeta. Requiere soporte ICU. Crea clúster temporal privado, genera contraseña efímera, escucha solo loopback y detiene/elimina únicamente sus propios archivos. No toca .env ni privilegios del rol de desarrollo. En Linux ejecutarlo como usuario normal. Para un servidor de pruebas preparado por el equipo también puede usarse `python backend/manage.py test inventory`; configurar explícitamente las variables de ese servidor y su rol, no elevar el de la aplicación.

Resultado original del incremento 002: 28 pruebas backend correctas, incluidas carreras reales PostgreSQL, permisos, CSRF, restricciones Unicode, rollback, inmutabilidad y rectificación. Detalles: [validation.md](../specs/002-registro-consulta-activos/validation.md).

Este es un entorno de desarrollo académico. El despliegue público, TLS, copias de seguridad y plazos institucionales de conservación no se declararon implementados. El historial no se borra automáticamente. Credenciales y datos reales deben permanecer fuera del repositorio.


## Extensión de licencias 006

Incluye SoftwareLicenseLot, auditoría inmutable, endpoints /api/license-lots/ y proveedor real para lotes de 008. Migraciones 0004/0005, sin modificar tablas de activos. En Linux el runner necesita `export PG_BIN=/usr/lib/postgresql/17/bin`; su socket y credenciales quedan en carpeta temporal privada.

Suite actual: 72 pruebas backend, más 16 puras de 008. Reproducción y avisos de seguridad de DRF en [validation.md](../specs/006-lotes-licencias/validation.md). [Quickstart](../specs/006-lotes-licencias/quickstart.md) incluye navegador real opcional sin instalar herramientas en el entorno de la aplicación. No recrear bases o gestores existentes.
