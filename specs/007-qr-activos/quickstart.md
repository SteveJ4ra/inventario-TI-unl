# Quickstart de QR — implementación 007 (actualizado 2026-11-04)

## Requisitos y preparación

- Seguir instrucciones generales de `backend/README.md` y `frontend/README.md`.
- Instalar Python y PostgreSQL según versiones del proyecto, además de Node/npm.
- Tener el rol Gestor habilitado mediante el comando de la base 002.
- Incluir en `backend/requirements.txt` `segno==1.6.6`.
- Configurar **solo localmente** en `backend/.env`: `PUBLIC_APP_URL=http://127.0.0.1:5173`.
- Documentar la variable también en `backend/.env.example` sin credenciales.

**Advertencia:** `127.0.0.1` solo sirve para pruebas en la misma PC. Para dispositivos externos o etiquetas finales, coordinar una URL **HTTPS** canónica realmente accesible y volver a generar los QR que proceda.

## Ejecutar la aplicación

Desde la raíz del repositorio, en terminales separadas:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
npm.cmd --prefix frontend run dev
```

Acceder a `http://127.0.0.1:5173/` como Gestor. Abrir la ficha de un activo real de prueba, pulsar «Descargar QR (SVG)» y verificar el SVG. Para el activo local de demostración, la URL fue `http://127.0.0.1:5173/assets/code/TI-000001` (no presupone que exista en otras instalaciones).

## Pruebas automatizadas

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory.test_qr_assets --verbosity 2
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py --verbosity 2
& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
& .\backend\.venv\Scripts\python.exe -m pip check
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
git diff --check
```

El 2026-11-04 se observaron **10/10** pruebas QR backend, **55/55** pruebas backend generales (incluyen las anteriores) y **25/25** pruebas frontend (incluye 5 del archivo `src/tests/qr.test.tsx`). Se observó Python 3.13.17 en entorno separado y `pip check` satisfactorio. Ver `validation.md` para límites.

## Aceptación manual y límites

1. **Comprobado manualmente por el alumno:** enlace QR en ventana sin sesión → login → ficha `TI-000001`.
2. Probar cuenta sin rol Gestor, código inexistente y destino externo no permitido; no revelar datos del activo.
3. **Parcial:** teléfono reconoció el enlace QR; no pudo abrir la aplicación porque el URL es `127.0.0.1`. El alumno confirmó las restantes pruebas manuales; falta anotar lector y dimensiones exactas y definir HTTPS accesible antes de etiquetas definitivas.
4. Probar QR de activos No localizado/Baja cuando esos estados estén integrados.

No marcar aceptación global hasta registrar las evidencias anteriores. Antes de ejecutar Spec Kit, seleccionar `specs/007-qr-activos` y comprobar `FEATURE_DIR`. El chequeo de prerrequisitos **no** ejecuta implementación ni pruebas.
