# Notas de integración — 007: QR de activos

**Fecha:** 2026-11-04  
**Rama propia:** `feature/pedro-007-qr-activos`  
**Base local de seguimiento de `origin/develop`:** `4247cc8998ed810fdb6462941d85f3324260a2ec` (salida real de `git rev-parse origin/develop` en la terminal del alumno).  
**Advertencia:** esta referencia no demuestra que la rama remota no tenga commits nuevos; ejecutar `git fetch origin` antes de abrir/actualizar el PR y volver a comprobar la base.

## 1. Proveedores y dependencias

| Paquete o contrato | Estado / implicación |
|---|---|
| 002: sesión Gestor, activo TI, ficha e historial | **Disponible y usado** en la instalación local. Las pruebas del backend (55/55) y frontend incluida QR (25/25) no encontraron regresiones. |
| 004/005: No localizado y Baja | **Integración pendiente**, según el alcance del encargo. La nueva búsqueda no debe filtrar por «Disponible». Probar al integrar esos estados; no crear sus modelos aquí. |
| Licencias | **Fuera del alcance:** no crear QR de licencias ni duplicar tablas de otros paquetes. |
| `docs/sdd` | La carpeta `docs/sdd/alcance-backend-completo.md` se comprobó existente en la rama de trabajo; no se verificó aprobación formal de la Constitución SDD. |

## 2. Interfaces entregadas a otros paquetes

- `GET /api/assets/{asset_id}/qr.svg`: SVG solo para Gestor; `200/403/404`, sin persistencia de imagen.
- `GET /api/assets/by-code/{code}/`: busca código TI exacto y devuelve el mismo contrato de ficha autenticada.
- `GET /assets/code/{code}` **en el cliente web**: conserva la ruta interna durante el login, sin exposición pública de ficha.
- `PUBLIC_APP_URL`: una variable por entorno; usar HTTPS en despliegue, no `Host` de la solicitud. Avisar al equipo antes de cambiar el dominio porque los QR impresos conservan enlaces anteriores.

## 3. Archivos compartidos y superficie de conflicto

**Modificados** según `git status --short` local: `backend/.env.example`, `backend/config/settings.py`, `backend/inventory/urls.py`, `backend/inventory/views.py`, `backend/requirements.txt`, `frontend/src/App.tsx`.  
**Nuevos**: `backend/inventory/qr_urls.py`, `backend/inventory/test_qr_assets.py`, `frontend/src/tests/qr.test.tsx`.  
**Solo local, no subir:** `backend/.env`, `backend/.venv`, `frontend/node_modules`, salida `dist`, archivos de base, SVG temporales y capturas con datos privados.

`views.py`, `urls.py`, `settings.py` y `App.tsx` pueden coincidir con otros paquetes. En integración, resolver conflictos conservando los dos aportes; no sustituir el archivo completo de otro estudiante ni reescribir rutas/modelos comunes sin revisar. Confirmar que el botón QR permanezca dentro de la ficha del activo existente.

## 4. Migraciones y datos

- Migraciones observadas de `inventory`: `0001_initial`, `0002_integrity`, `0003_importbatch`; sin nuevas migraciones del paquete QR.
- `makemigrations --check --dry-run` => `No changes detected`.
- Las pruebas de regresión utilizaron el runner con PostgreSQL temporal `test_postgres`, que se eliminó tras ejecutarse.
- El activo de ejemplo `TI-000001` fue creado en la **base local de desarrollo**; no se transporta como dato obligatorio a la rama ni al despliegue.
- No otorgar `CREATEDB` a `inventario_app`, no recrear ni borrar la base de otros integrantes.

## 5. Regresiones ya observadas

| Comando | Resultado |
|---|---|
| `& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory.test_qr_assets --verbosity 2` | 10/10 PASS |
| `& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py --verbosity 2` | 55/55 PASS, incluyendo las anteriores |
| `npm.cmd --prefix frontend test -- --run` | 25/25 PASS, incluye 5 pruebas frontend QR |
| `npm.cmd --prefix frontend run build` | PASS |
| `& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run` | PASS |
| `& .\backend\.venv\Scripts\python.exe -m pip check` | PASS |
| `git diff --check` | PASS |

## 6. Acciones para auditoría y PR

1. **Confirmado:** `backend/.venv` inicial usa Python 3.12.3; un entorno adicional usa Python 3.13.17 y `pip check` pasó. La captura de 55/55 no expone el comando de la ejecución final; consignarlo claramente cuando se adjunte al PR.
2. **Realizado:** `backend/.env.example` documenta `PUBLIC_APP_URL` y Git detectó su modificación. Añadir solo `.env.example`, nunca `backend/.env`.
3. **Realizado:** alumno confirmó sin sesión → login → ficha y se añadieron 5 pruebas frontend QR (25/25 en suite). Conservar evidencias sin secretos.
4. **Pendiente de coordinación/registro:** el móvil reconoció el enlace codificado, pero no puede abrir `127.0.0.1` en la PC. Acordar `PUBLIC_APP_URL` HTTPS definitivo; documentar dimensiones y lector de las etiquetas impresas antes de cerrar aceptación.
5. Revisar estados 004/005 al integrarse; repetir la suite y resolver conflictos compartidos sin borrar historia.
6. Revisar `git status`, `git diff`, migraciones y prueba completa; abrir PR **hacia `develop`**, sin autoaprobar ni fusionar. Considerar **Draft PR** si las validaciones de integración siguen bloqueadas.
7. Solicitar revisión de otro integrante y registrar observaciones. No marcar Constitución como ratificada por IA.

**Evaluación:** No se observó bloqueo técnico para continuar en la rama propia. La integración/aceptación global no está aprobada y tiene verificaciones pendientes explícitas.
