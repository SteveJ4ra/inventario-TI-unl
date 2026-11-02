# Evidencia backend 005

**Fecha:** 1 de noviembre de 2026. Pruebas con backend/.venv/Scripts/python.exe desde raíz del repositorio.

| Comando | Resultado | Límite |
|---|---|---|
| `backend/tools/test_postgres.py` | PASS 44 tests | Configuración normal: regresión 002, comando, validadores y permisos aislados. Incluye aplicación de 0003_retirement_movement_type. |
| `backend/tools/test_postgres.py contract_tests --settings=contract_tests.settings --verbosity 1` | PASS 24 tests | PostgreSQL real y código 005 con proveedores mínimos de prueba de 003/004; esquema creado por syncdb, no prueba migraciones finales. |
| `-m unittest discover -s backend/inventory/isolated_tests/approval -p "test_*.py" -v` | PASS 21 tests | Políticas/orquestación con dobles solo de pruebas; no demuestra SQL por sí solo. |
| `backend/manage.py makemigrations --check --dry-run` | PASS No changes detected | Solo modelos registrados en configuración normal; no cubre los modelos 005 aún sin activar allí. |
| `-m pip check` | PASS | Sin requisitos rotos en venv. |
| `git diff --check` | PASS | Formato, no comportamiento. |

Suite de contrato: solicitud pendiente única/no autoasignación; decisión/razón/triggers; baja normal/aprobada; rollback exterior; rectificación normal/aprobada conservando evidencia; permisos por asignación; contraseña temporal/cambio efectivo; CSRF/sesión/métodos; creación y desactivación de revisores; reasignación antes de desactivar; mantenimiento activo bloquea baja; snapshots sobreviven renombrado; cambio de facultad bloqueado; carreras de doble baja, doble solicitud y recuperación frente a aprobación con conexiones PostgreSQL independientes.

No se ha probado contra las implementaciones reales de Alex/Yandri ni desplegado/activado 005 en la aplicación normal. No se afirma que la migración final o todos los escenarios de validation-plan estén aprobados. Frontend fuera del alcance actual.
