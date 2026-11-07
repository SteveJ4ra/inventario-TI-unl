# Trazabilidad del flujo priorizado

Los identificadores HU, CA y RNF corresponden al dossier de semana 2; los FR llevan el prefijo del incremento para evitar ambigüedad.

| Necesidad y requisito | Criterio | Componente C3 y decisión | Operación versionada | Evidencia de prueba |
| --- | --- | --- | --- | --- |
| Identificar equipo: HU-01, 002/FR-002 y FR-015 | CA-01: alta disponible y sin custodio | API, servicios de adquisición y modelos; ADR-0301 y ADR-0304 | POST /api/v1/assets/ | test_api_v1.py: test_asset_cycle_and_legacy_contract |
| Consultar situación: HU-01, 002/FR-009 | Búsqueda y ficha coherentes con el alta | API y adaptador v1; ADR-0303 y ADR-0306 | GET /api/v1/assets/ y /assets/{asset_id}/ | test_api_v1.py: test_asset_cycle_and_legacy_contract |
| Controlar custodia: HU-02, 002/FR-012 | CA-02: entregar solo cuando corresponde | API, permisos y servicios; ADR-0302 y ADR-0305 | POST /api/v1/assets/{asset_id}/deliver/ | test_custody.py: test_invalid_states_stale_revision_and_forged_author |
| Recibir activo: HU-02, 002/FR-013–FR-014 | CA-03: registrar condición, ubicación e historial | Servicios, modelos y PostgreSQL; ADR-0302 | POST /api/v1/assets/{asset_id}/return/ | test_api_v1_live.py: recorrido HTTP con sesión y CSRF |
| Ver cambios de otro gestor: observación confirmada de ACD 3 | La siguiente consulta exitosa actualiza la página seleccionada | Página de API y API v1; ADR-0303 y ADR-0306 | GET /api/v1/assets/?page=N desde /api/docs/ | docs-live.test.js: actualización periódica y pérdida de acceso; comprobación Chrome de dos sesiones |
| Conservar compatibilidad y acceso: RNF-01 y RNF-05 | Rechazar acceso no autorizado y preservar /api/ | Permisos y adaptador v1; ADR-0303 y ADR-0305 | Rutas v1 y rutas históricas | test_api_v1.py: errores, CSRF y compatibilidad |

El esquema OpenAPI exportado y el servido deben coincidir. Los archivos de código y las pruebas se encuentran en `backend/inventory/`; la prueba de la página visual está en `frontend/src/tests/docs-live.test.js`. La comprobación Chrome se ejecutó como verificación local adicional; las pruebas versionadas permiten repetir los controles de API y actualización con el entorno descrito.
