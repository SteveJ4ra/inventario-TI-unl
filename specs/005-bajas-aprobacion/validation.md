# Validación 005: evidencia parcial

**Fecha:** 1 de noviembre de 2026. No se validó el flujo integral de bajas ni se autoriza su uso.

| Verificación | Resultado | Alcance |
|---|---|---|
| `python -m unittest discover -s backend/inventory/isolated_tests/approval -p "test_*.py" -v` | PASS: 13 pruebas | Reglas y orquestación con doble en memoria; no valida transacciones ni API reales. |
| `backend/tools/test_postgres.py inventory.tests.test_deactivate_gestor --verbosity 2` | PASS: 2 pruebas | PostgreSQL temporal; desactivación, acceso y autoría. |
| `backend/tools/test_postgres.py` | PASS: 30 pruebas | Base 002 y comando de desactivación; no implementa endpoints 005. |
| `npm.cmd --prefix frontend test -- --run` | PASS: 24 pruebas | Suite completa después de agregar los casos de baja/contraseña. |
| `npm.cmd --prefix frontend test -- --run src/tests/reviewer-admin.test.tsx src/tests/retirement-components.test.tsx` | PASS: 7 pruebas | Componentes aislados con callbacks de prueba, no conectados a API. |
| `npm.cmd --prefix frontend run build` | PASS | Compilación; los componentes aislados aún no se montan en App. |
| Integración de 003/004 y flujos API/DB/UI 005 | DEPENDENCIA NO INTEGRADA | Faculty/Operador de 003 y lifecycle/recuperación de 004 no están en develop; falta implementación real del adaptador. |

El runner usa PostgreSQL temporal aislado; no se alteró la base local. Las pruebas con dobles no prueban concurrencia real de aprobación/recuperación, permisos de reviewer ni seguridad del backend.
