
# Backend — Inventario de Tecnologías de Información

Backend del proyecto Inventario de Tecnologías de Información, desarrollado como parte de la asignatura Desarrollo Basado en Plataformas de la Universidad Nacional de Loja.

Esta configuración inicial permite ejecutar Django con Django REST Framework y conectarlo a una base de datos PostgreSQL. Las funcionalidades específicas de gestión de activos se implementarán posteriormente.

## 1. Tecnologías utilizadas

- Python 3.13
- Django 5.2
- Django REST Framework 3.16
- PostgreSQL 17
- psycopg 3
- python-dotenv

Las versiones exactas de las dependencias de Python se encuentran en `requirements.txt`.

## 2. Requisitos previos

Antes de comenzar, instalar:

- Python 3.13
- PostgreSQL 17
- Git

Los comandos siguientes están orientados a Windows PowerShell. Para otros sistemas operativos será necesario adaptar la activación del entorno virtual y la administración de PostgreSQL.

## 3. Preparar el entorno virtual

Desde la raíz del repositorio:

```powershell
python -m venv backend\.venv
```

Activar el entorno:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, se puede habilitar temporalmente para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después, repetir el comando de activación.

## 4. Instalar las dependencias

Con el entorno virtual activado:

```powershell
python -m pip install -r backend\requirements.txt
```

## 5. Configurar PostgreSQL

Iniciar PostgreSQL y acceder mediante su usuario administrador:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5432 -d postgres
```

Dentro de `psql`, crear un usuario para la aplicación:

```sql
CREATE ROLE inventario_app WITH LOGIN;
```

Asignar una contraseña de forma interactiva:

```text
\password inventario_app
```

Crear la base de datos:

```sql
CREATE DATABASE inventario_ti OWNER inventario_app ENCODING 'UTF8';
```

Salir de PostgreSQL:

```text
\q
```

Si el usuario o la base de datos ya existen, no es necesario crearlos nuevamente.

## 6. Configurar las variables de entorno

Desde la raíz del repositorio, copiar el archivo de ejemplo:

```powershell
Copy-Item backend\.env.example backend\.env
```

Editar `backend/.env` y completar los valores necesarios:

- `DJANGO_SECRET_KEY`: clave secreta de Django.
- `DJANGO_DEBUG`: usar `True` para el desarrollo local.
- `DB_NAME`: nombre de la base de datos.
- `DB_USER`: usuario de PostgreSQL.
- `DB_PASSWORD`: contraseña del usuario.
- `DB_HOST`: servidor de PostgreSQL.
- `DB_PORT`: puerto de PostgreSQL.

Para generar una clave secreta de Django:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copiar la clave generada al archivo privado `backend/.env`.

**No publicar `backend/.env`, contraseñas ni claves secretas en GitHub.**

## 7. Preparar la base de datos

Desde la raíz del repositorio, con el entorno virtual activado:

```powershell
python backend\manage.py check
```

Aplicar las migraciones iniciales:

```powershell
python backend\manage.py migrate
```

Estas migraciones preparan las tablas predeterminadas de Django. Todavía no crean modelos propios del inventario.

## 8. Ejecutar el servidor de desarrollo

```powershell
python backend\manage.py runserver 127.0.0.1:8000
```

Abrir en el navegador:

http://127.0.0.1:8000/

Si la configuración inicial funciona, Django mostrará su página predeterminada.

Para detener el servidor, presionar `Ctrl + C` en PowerShell.

## 9. Estado del desarrollo

La configuración inicial incluye:

- Proyecto Django creado.
- Django REST Framework registrado.
- Conexión a PostgreSQL mediante variables de entorno.
- Dependencias registradas.
- Migraciones iniciales de Django.
- Servidor de desarrollo local.

Todavía están pendientes los modelos de activos, las reglas del negocio, los endpoints del inventario y las pruebas funcionales.

## 10. Consideraciones de seguridad

- Utilizar credenciales locales para cada instalación.
- Mantener el archivo `.env` fuera del control de versiones.
- No utilizar el usuario administrador `postgres` como usuario de la aplicación.
- Mantener `DJANGO_DEBUG=True` únicamente en desarrollo local.
- No considerar esta configuración como preparada para producción.
