# Validación final de 004

Ejecutada el 4 de noviembre de 2026 en Windows con Python 3.13.12, Django 5.2.18, PostgreSQL 17.11 con ICU, Node 24.18.0 y npm 11.16.0.

## Comandos y resultados

| Comando desde la raíz | Resultado |
|---|---|
| `& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory --verbosity 1` | PASS. 83 pruebas en PostgreSQL temporal con ICU, incluidas regresiones de 002 y 004 y el caso explícito de bloqueo tras mantenimiento correctivo. |
| `npm.cmd --prefix frontend test -- --run` | PASS. 26 pruebas en 11 archivos. Los recorridos de componentes usan jsdom y una API simulada. |
| `npm.cmd --prefix frontend run build` | PASS. Compilación TypeScript y build de Vite. |
| `& .\backend\.venv\Scripts\python.exe backend/manage.py check` | PASS. Cero problemas. |
| `& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run` | PASS. `No changes detected`. |
| `& .\backend\.venv\Scripts\python.exe backend/manage.py showmigrations inventory` | PASS. `0001`–`0005` aplicadas en el entorno local. |
| `& .\backend\.venv\Scripts\python.exe backend/manage.py migrate --plan` | PASS. Cero operaciones pendientes. |
| `git diff --check` | PASS. Sin avisos. |

La conexión configurada por Django devolvió `inventario_ti`, `inventario_app` y proveedor de locale `i` (ICU) al consultar `current_database()`, `current_user` y `pg_database.datlocprovider`. Las escrituras de las pruebas se hicieron exclusivamente en clústeres temporales.

## Aceptación y regresiones

| Caso | Evidencia |
|---|---|
| SC-001, daños con custodia vigente | API sobre PostgreSQL y Chrome real. Registro y resolución conservan condición y custodia, registran autoría y mantienen ambas entradas. |
| SC-002 y SC-003, taller | API sobre PostgreSQL para mantenimiento preventivo y correctivo, rechazo de entrega, revisión obsoleta y rollback. Chrome comprobó bloqueo en la ficha, precarga de ubicación, edición y confirmación explícita. |
| SC-004, pérdida o robo | API sobre PostgreSQL desde Disponible, Asignado y taller. Chrome verificó robo en taller, último estado e interrupción sin resultado. |
| SC-005, recuperación | API sobre PostgreSQL y Chrome real. Inspección, condición, ubicación, mismo código, sin custodia vigente ni reactivación. |
| FR-015–FR-016, integridad y evidencia | Suite PostgreSQL con 403 de permisos y CSRF, 400 de validación, 404, 409, carreras de entrega/inicio y recuperación, rollback provocado, trigger contra actualización/borrado y migración con filas legadas. Las pruebas de rollback inyectan un fallo de escritura para verificar la reversión de la transacción. |
| Regresión 002 | Suite completa de inventario. Chrome comprobó entrega y devolución reales, pérdida de elegibilidad de rectificación tras un evento 004 y formato legado de movimientos. |

## Integración real en navegador

Se ejecutó el escenario [browser.cjs](checks/browser.cjs) con Chrome instalado, Playwright, React servido por Vite, Django con sesión y CSRF reales y PostgreSQL temporal con ICU. No hubo respuestas HTTP simuladas en este recorrido.

```powershell
$env:VALIDATION_004_PLAYWRIGHT="$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright"
$env:VALIDATION_004_CHROMIUM='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .\backend\.venv\Scripts\python.exe backend/tools/validate_004_browser.py
```

Resultado PASS, salida 0. Se verificaron entrega, daño asignado, resolución, devolución, inicio y cierre con recepción editada, segundo inicio, robo, interrupción y recuperación. La API devolvió diez revisiones consecutivas en orden descendente. El historial legado contenía solo la entrega y devolución reales. No hubo errores JavaScript de página.

## Pendientes

Quedan pendientes la reproducción y revisión humana por otro integrante, la aceptación institucional y la integración con solicitudes de baja de 005. Los casos CSV de la suite mantienen el gateway de prueba que ya usaba 008. Los resultados no certifican los proveedores de 003/006 ni el despliegue productivo.
