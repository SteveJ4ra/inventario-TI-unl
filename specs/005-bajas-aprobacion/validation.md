# Validación 005: evidencia parcial

**Fecha:** 1 de noviembre de 2026. No se validó el flujo integral de bajas ni se autoriza su uso.

| Verificación | Resultado | Alcance |
|---|---|---|
| `python -m unittest discover -s backend/inventory/isolated_tests/approval -p "test_*.py" -v` | PASS: 13 pruebas | Reglas y orquestación con doble en memoria; no valida transacciones ni API reales. |
| `backend/tools/test_postgres.py inventory.tests.test_deactivate_gestor --verbosity 2` | PASS: 2 pruebas | PostgreSQL temporal; desactivación, acceso y autoría. |
| `backend/tools/test_postgres.py` | PASS: 30 pruebas | Base 002 y comando de desactivación; no implementa endpoints 005. |
| `backend/tools/test_postgres.py inventory.tests.test_retirement_serializers inventory.tests.test_retirement_permissions --verbosity 2` | PASS: 9 pruebas | Validación estricta y permisos aislados; no prueba endpoints reales. |
| Frontend | FUERA DEL ALCANCE ACTUAL | Los componentes añadidos previamente se retiraron por indicación del usuario; sus antiguas pruebas no se atribuyen a la versión actual. |
| Integración de 003/004 y flujos API/DB 005 | DEPENDENCIA NO INTEGRADA | Faculty/Operador de 003 y lifecycle/recuperación de 004 no están en develop; falta implementación real del adaptador. |

El runner usa PostgreSQL temporal aislado; no se alteró la base local. Las pruebas con dobles no prueban concurrencia real de aprobación/recuperación, permisos de reviewer ni seguridad del backend.
