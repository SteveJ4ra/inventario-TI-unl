# Validación de 006 — evidencia local

Fecha: 2026-11-04, America/Guayaquil. Ejecutor: Codex con autorización de Anderson; revisión humana pendiente. No se usa SQLite ni un fake como proveedor de producción.

Entorno principal comprobado: Python 3.13.14, Django 5.2.18, DRF 3.18.2, psycopg 3.3.6, PostgreSQL 17.11 con ICU, Node 24.18.0, npm 11.16.0, PowerShell 7.6.9, Chrome 156.0.8078.47. Dependencias frontend conservadas según package-lock. La instalación inicial usaba DRF 3.16.1; la actualización puntual a 3.18.2 fue autorizada por Anderson, aplicada y comprobada con todos los comandos repetidos. Se conserva el historial del hallazgo inicial abajo.

## Comandos y resultados

Todos desde la raíz. PG_BIN se indica por comando para no depender de variables de otra terminal.

| Comando exacto | Resultado real |
|---|---|
| `SPECIFY_FEATURE_DIRECTORY=specs/006-lotes-licencias SPECIFY_FEATURE_NO_PERSIST=1 pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | PASS: FEATURE_DIR correcto y archivos requeridos. Solo comprobación documental. |
| `PG_BIN=/usr/lib/postgresql/17/bin PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/tools/test_postgres.py --verbosity 1` | PASS: 72 pruebas; 27 de 006 y 45 de regresión. Migraciones y carreras en PostgreSQL real efímero. |
| `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -m unittest discover -s backend/inventory/isolated_tests/imports -p 'test_*.py' -v` | PASS: 16 pruebas puras existentes de 008. No son evidencia de DB real. |
| `backend/.venv/bin/python backend/manage.py check` | PASS: 0 incidencias. |
| `backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run` | PASS: No changes detected. |
| `backend/.venv/bin/python -m pip check` | PASS: No broken requirements found. No sustituye auditoría de CVE. |
| `npm --prefix frontend test -- --run` | PASS: 33 pruebas en 9 archivos; 13 nuevas de 006 y 20 existentes. Red simulada en estos tests. |
| `npm --prefix frontend run build` | PASS: TypeScript y Vite; 27 módulos. Build local, sin despliegue. |
| `PG_BIN=/usr/lib/postgresql/17/bin uv run --no-project --with playwright python backend/tools/smoke_license_lots.py` | PASS: Chrome real, backend real y PostgreSQL efímero, sin fake de dominio. Recorrido detallado abajo. |
| `npm --prefix frontend audit --json` | PASS: 0 avisos reportados. Resultado de la base de avisos consultada en esta fecha. |
| `uvx --from bandit bandit -q -r backend/inventory -ll -x backend/inventory/tests,backend/inventory/isolated_tests` | PASS: salida 0, sin hallazgos medios/altos. Análisis estático, no pentest. |
| `uvx --from pip-audit pip-audit --no-deps --disable-pip -r backend/requirements.txt` | PASS final: sin vulnerabilidades conocidas en los requirements actualizados. Ejecución inicial FAIL con cinco avisos en DRF 3.16.1, conservada en la sección de dependencia; sin ignorar IDs. |
| `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/manage.py check --deploy` | ADVERTENCIAS: W004/W008/W012/W016/W018 por HSTS, redirección HTTPS, cookies Secure y DEBUG. Es configuración local HTTP; no se declara producción segura. |
| `git diff --check` | PASS sin errores de whitespace. |

## Casos por requisito

Ejecutar cada clase con `PG_BIN=/usr/lib/postgresql/17/bin backend/.venv/bin/python backend/tools/test_postgres.py inventory.tests.test_license_lots.<Clase> --verbosity 2`.

| FR / SC | Clase / caso comprobado | Evidencia |
|---|---|---|
| FR-001/002/009/012 | LicenseLotApiTests: altas, detalle, campos reservados y métodos | 201/200; 400 ante claves/activos/custodios/facturas; 405 en PUT/DELETE; modelos sin esas asociaciones. |
| FR-003/004, SC-001/002 | LicenseLotModelTests, LicenseLotServiceTests, LicenseLotApiTests | 10−4=6, 0/0 válido; negativos, bool, float, cadenas y exceso de uso rechazados; constraints PostgreSQL aun sin API. |
| FR-005/006/007, SC-003/004 | ModelTests y ApiTests.test_dates_filters_and_output_use_same_local_day | Inicio obligatorio; fin null; fin inclusivo; futuro/vigente/vencido; mismo resultado entre filtro y salida en UTC/Guayaquil cerca de medianoche. Remanentes persisten al vencer. |
| FR-008, SC-005 | ServiceTests y ModelTests.test_audit_is_immutable_in_orm_bulk_sql_and_unique_per_revision | Los siete campos antes/después, actor/fecha/revisión; etiqueta histórica conservada tras renombrar cuenta; bloqueo de save/delete, bulk update/delete y DELETE SQL. |
| FR-008/010 | LicenseLotConcurrencyTests | Dos conexiones y barrera real: un ganador y un 409; una revisión nueva, sin auditoría parcial. |
| FR-010 | ApiTests.test_all_routes_require_active_manager_even_for_superuser y test_other_managers_have_equal_access | Anónimo, inactivo, no gestor y superusuario sin Gestores reciben 403; otro gestor sí consulta/edita. Los grupos ajenos son fixtures, no implementación de 003/005. |
| FR-010 | ApiTests.test_real_session_requires_csrf_and_rejects_foreign_origin | Sesión real: POST/PATCH sin CSRF y origen ajeno rechazados con 403; token válido permite PATCH; logout revoca acceso. |
| FR-011 | ApiTests.test_search_combined_filters_injection_and_query_validation y test_pagination_history_and_read_methods_do_not_write | Producto/proveedor, AND de filtros, 50 registros por página, 400 en query inválida, búsqueda con texto SQL no ejecuta SQL; GET no crea eventos. |
| FR-003/008/010 | ServiceTests.test_audit_failure_rolls_back_create_and_edit | Fallo inyectado exclusivamente en el escritor de auditoría; alta/edición revertidas en PostgreSQL real. |
| Proveedor 008 | LicenseLotRealImportTests, LicenseLotAtomicImportReviewTests | CSV real → preview sin escrituras → dos confirmaciones → alta real; reintento idempotente. Fallo en segunda fila revierte lotes/eventos y batch, luego permite reintentar. |
| Proveedor 008 | SecurityReviewTests.test_real_import_preview_uses_provider_limits_before_confirmation | Cantidad fuera de integer rechazada en preview mediante validador de 006, sin filas de dominio. |
| Robustez OWASP | LicenseLotSecurityReviewTests, LicenseLotCharsetTests, LicenseLotMalformedJsonReviewTests | JSON acotado, UTF-8, no-store, entradas anidadas/malformadas, surrogates en campos/valores: 400 sin escrituras, sin 500. |
| FR-001–011 web | `npm --prefix frontend test -- --run src/tests/license-lots.test.tsx` | 13 pruebas de formularios, preview, filtros, páginas, estado, historia, errores, PATCH/CSRF, 409 sin reintento, XSS como texto, 403 y logout. |

## Navegador real

El script versionado arranca sus propios servidores en puertos libres y su PostgreSQL privado. Usa dos gestores ficticios con contraseña aleatoria efímera. Se comprobó: login; alta 0/0 sin fin; edición a 10/4; fin anterior a hoy → Vencido con 6 remanentes; historial antes/después; otro gestor cambia a 2; edición obsoleta del primero → 409, recarga y 8 remanentes; tres eventos totales, sin evento del rechazo; PATCH sin CSRF → 403; navegación visible a 375px, sin desborde horizontal; logout vuelve al login. Sin errores JavaScript no controlados. La captura sintética móvil se inspeccionó; no se guarda información del usuario ni se versionan capturas privadas.

## Migraciones locales y datos existentes

Antes de aplicar se ejecutaron `backend/.venv/bin/python backend/manage.py migrate --plan`, `sqlmigrate inventory 0004` y `sqlmigrate inventory 0005`. Solo se agregan tablas, FK de autor/lote y restricciones/trigger de licencias. Aplicación real con `backend/.venv/bin/python backend/manage.py migrate --noinput`: ambas OK. Hashes de todas las filas previas de Asset, Custodian, Movement, ImportBatch y User coinciden antes/después. Había 0 filas de negocio y 1 cuenta. Nuevas tablas quedan vacías; fixtures de navegador/API solo existieron en DB efímera.

## Dependencia: hallazgo inicial y corrección aplicada

El escaneo de DRF 3.16.1 reportó PYSEC-2026-3827 (CVE-2026-73228), PYSEC-2026-3828 (CVE-2026-73229), CVE-2026-114138, CVE-2026-114136 y CVE-2026-114137. La [publicación oficial 3.18.2](https://github.com/encode/django-rest-framework/releases/tag/3.18.2) y el [aviso del parser](https://github.com/encode/django-rest-framework/security/advisories/GHSA-3547-9m27-7rxg) documentan correcciones. La autenticación TokenProxy no se usa en esta app, pero el aviso de paquete se conserva; los riesgos de parser/negociación no se dan por resueltos globalmente por endurecer solo 006.

Propuesta preparada en `/tmp/inventario006-security-requirements.txt`: mismos requirements, únicamente DRF 3.18.2. Comando `PG_BIN=/usr/lib/postgresql/17/bin PYTHONDONTWRITEBYTECODE=1 uv run --no-project --python 3.13 --with-requirements /tmp/inventario006-security-requirements.txt python backend/tools/test_postgres.py --verbosity 1`: PASS 72 pruebas. `uvx --from pip-audit pip-audit --no-deps --disable-pip -r /tmp/inventario006-security-requirements.txt`: PASS sin avisos conocidos. Esa fue la comprobación previa en una variante temporal. Después Anderson autorizó aplicar únicamente DRF 3.18.2: se cambió requirements y se instaló con `backend/.venv/bin/python -m pip install --no-deps 'djangorestframework==3.18.2'`. Comparación de distribuciones antes/después: solo djangorestframework cambió, de 3.16.1 a 3.18.2. Con la instalación principal actualizada se repitieron las 72 pruebas backend, 33 frontend, 16 puras, build, navegador real, check/makemigrations/pip check, npm audit, pip-audit y Bandit. Todos los resultados funcionales son PASS; las auditorías no reportan avisos conocidos en el alcance indicado. Se conserva el lockfile y las demás versiones. No se ignoran vulnerabilidades para obtener un resultado favorable.

## Fallos encontrados y corregidos

1. Runner original: permiso denegado al crear socket en /var/run/postgresql; resuelto con socket privado y diagnóstico del log. Línea base: 45 PASS.
2. JSON escalar: error heredado al convertir lista de errores a diccionario; serializador 006 devuelve non_field_errors estructurado.
3. Preview de 008 no aplicaba el rango del proveedor: delegación mínima a 006 y regresión real. Una importación faltante durante la reducción del diff se corrigió antes del resultado final.
4. Primer intento del navegador no localizó la modalidad: nombre accesible explícito; recorrido posterior PASS.
5. Campo Unicode surrogate: error 500 de representación; validación de claves UTF-8 y regresión PASS.

## Límites

NO EJECUTADO: aceptación manual por Anderson y revisión por otro integrante. DEPENDENCIA NO INTEGRADA: activos/adquisiciones 003 para esa modalidad de CSV; no bloquea lotes de 006. No se probaron infraestructura pública, TLS, proxy de producción, carga destructiva, todas las vulnerabilidades posibles ni un pentest OWASP completo. La [guía OWASP API Security](https://api-security.owasp.org/editions/2023/en/0x11-t10/) orientó los controles aplicables; no es certificación ni garantía de ausencia de vulnerabilidades. La Constitución sigue propuesta.
