# Quickstart: validar 006 localmente

Requiere el entorno del README, PostgreSQL 17 con ICU, dependencias instaladas y .env privado. No hay credenciales compartidas. La DB local preparada por Anderson escucha en 55432; el runner usa un puerto temporal distinto y no consulta sus datos.

Desde raíz en Linux:

```bash
source backend/.venv/bin/activate
export PG_BIN=/usr/lib/postgresql/17/bin
export SPECIFY_FEATURE_DIRECTORY=specs/006-lotes-licencias
export SPECIFY_FEATURE_NO_PERSIST=1
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
python backend/manage.py check
python backend/manage.py migrate --plan
```

Revisar el plan antes de aplicar a otra copia. En esta copia 0004/0005 ya fueron aplicadas y la cuenta existente se conservó; no recrear base, usuario ni gestor.

```bash
python backend/manage.py migrate
python backend/tools/test_postgres.py
python backend/manage.py makemigrations --check --dry-run
python -m pip check
python -m unittest discover -s backend/inventory/isolated_tests/imports -p 'test_*.py' -v
npm --prefix frontend test -- --run
npm --prefix frontend run build
git diff --check
```

Prueba focalizada: `python backend/tools/test_postgres.py inventory.tests.test_license_lots --verbosity 2`.

## Recorrido de aceptación humana (pendiente de repetir por el alumno)

Ejecutar Django y Vite simultáneamente, en terminales diferentes: `python backend/manage.py runserver 127.0.0.1:8000` y `npm --prefix frontend run dev`. Abrir http://127.0.0.1:5173/ y usar un Gestor autorizado. El 404 en la raíz de 8000 es esperado.

1. Abrir Licencias; comprobar lista vacía o datos reales existentes.
2. Crear USER_SEAT con 10 compradas, 4 en uso, inicio pasado y sin fin: 6 remanentes y Vigente. También se admite 0/0.
3. Editar fin al día anterior, conservando inicio anterior: Vencido y 6 remanentes, con aviso de que no son puestos utilizables.
4. Consultar auditoría: alta y edición, autor, tiempo y los siete valores antes/después. Cambiar producto/proveedor/modalidad/fechas y verificar que también se auditan.
5. Intentar omitir inicio, usar negativos/fracciones, uso mayor que compra o fin anterior al inicio: rechazo sin cambio ni auditoría adicional. El fin puede quedar vacío.
6. Editar a 3 en uso: 7 remanentes; comprobar que PATCH utiliza la revisión actual.
7. Crear DEVICE_SEAT; buscar producto/proveedor, combinar modalidad/estado y limpiar. Si hay más de 50 registros, comprobar páginas.
8. Dos gestores abren el mismo lote antes de editar. Uno guarda; el segundo recibe conflicto, ve la ficha recargada y debe volver a editar conscientemente.
9. Usuario sin Gestores: datos y escrituras denegados; cerrar sesión elimina la vista privada.
10. Reducir ventana a 375px: navegación, formulario, detalle e historial utilizables.

## Recorrido automatizado con navegador real

Sin modificar la DB local ni agregar Playwright a package.json/requirements:

```bash
PG_BIN=/usr/lib/postgresql/17/bin uv run --no-project --with playwright python backend/tools/smoke_license_lots.py
```

Requiere Chrome local (`LICENSE_SMOKE_CHROME` permite indicar otro ejecutable). El script crea PostgreSQL, usuarios y procesos propios efímeros; comprueba alta cero, edición, vencimiento, dos gestores/conflicto, CSRF, móvil y logout. Limpia solo los recursos que crea. Es automatización de navegador, no aceptación humana ni certificado OWASP.

Resultados y límites reales: [validation.md](validation.md), [cinco revisiones](reviews.md), [integración](integration-notes.md).
