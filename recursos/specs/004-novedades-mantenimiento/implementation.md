# Implementación del paquete 004

El 4 de noviembre de 2026 se cerraron T001–T017 en la rama `feature/yandri-004-novedades-mantenimiento`, sobre la base local `develop` en `4247cc8998ed810fdb6462941d85f3324260a2ec`. El alcance corresponde a las historias US1–US3 y a FR-001–FR-016 de [spec.md](spec.md).

| Tareas | Alcance implementado |
|---|---|
| T001–T005 | Estados de localización, restricciones de custodia, modelos de eventos, revisión global, evidencia inmutable y rutas de consulta. |
| T006–T008 | FR-001–FR-004. Daños y observaciones con alertas, resolución con nota y autoría, sin cambios automáticos en la ficha. |
| T009–T012 | FR-005–FR-009. Inicio, bloqueo de entrega, cierre con ubicación de recepción confirmada y condición independiente. |
| T013–T016 | FR-010–FR-014. Pérdida o robo, snapshot de último estado conocido, interrupción de taller y recuperación con inspección, código conservado y custodia vigente nula. |
| T017 | FR-015–FR-016 como verificación transversal. Contratos, historial, quickstart, evidencias de validación y preparación del PR. |

## Decisiones técnicas

- `inventory.0004_asset_lifecycle_events` conserva el estado de activos previos como Localizado y amplía la restricción de custodia. Crea Incident, MaintenanceEvent y RecoveryEvent.
- `inventory.0005_asset_transition_evidence` crea AssetTransition, con evidencia antes/después, revisión y autoría. Su trigger PostgreSQL impide actualizar o borrar filas. Se conserva el trigger legado de Movement.
- Las operaciones comparten el bloqueo de la fila del activo y validan `expected_revision`. La pérdida en taller registra pérdida e interrupción con revisiones consecutivas en una sola transacción. El historial unificado usa revisión descendente y fecha, tipo e ID como desempate, conforme al contrato transversal. La frase anterior del contrato local que mencionaba solo fecha se precisó en [contracts/api.md](contracts/api.md).
- La ficha existente presenta daños, mantenimiento, último estado conocido y recuperación. Reutiliza el historial y cliente HTTP de la aplicación. No requiere un catálogo nuevo de ubicaciones.
- El [contrato de API](contracts/api.md) enumera rutas, campos y códigos. La base Django y los endpoints de movimientos de 002 siguen siendo el soporte del flujo.

## Archivos para revisión

| Área | Rutas desde la raíz |
|---|---|
| API y dominio | `backend/inventory/models.py`, `serializers.py`, `services.py`, `urls.py`, `views.py` |
| Esquema | `backend/inventory/migrations/0004_asset_lifecycle_events.py`, `0005_asset_transition_evidence.py` |
| Pruebas backend | `backend/inventory/tests/test_asset_transitions.py`, `test_concurrency.py`, `test_incidents.py`, `test_lifecycle_migration.py`, `test_maintenance.py` |
| Interfaz | `frontend/src/App.tsx`, `types.ts`, `styles.css`; componentes `Form.tsx`, `History.tsx`, `IncidentPanel.tsx`, `Inventory.tsx`, `MaintenancePanel.tsx` y `Movements.tsx` |
| Pruebas frontend | `frontend/src/tests/fixtures.ts`, `incidents.test.tsx`, `maintenance.test.tsx`, `queries.test.tsx`, `recovery.test.tsx` |
| Recorrido real | `backend/tools/validate_004_browser.py` y [checks/browser.cjs](checks/browser.cjs) |
| Documentación | `README.md`, y en 004 `contracts/api.md`, `quickstart.md`, `tasks.md`, `implementation.md`, `validation.md`, `integration-notes.md`, `pr-description.md` |

## Participación y revisión

Codex asistió en la implementación, pruebas, recorrido real automatizado y documentación. El usuario revisó avances por bloque y autorizó por separado las migraciones 0004 y 0005. La revisión del PR por otro integrante y la ratificación de la Constitución y del alcance por el equipo siguen pendientes. La [validación](validation.md) separa los resultados reales, los casos con dobles de prueba y la integración pendiente.
