# Catálogo del backend y contratos

Rutas inspeccionadas en el resolver Django de la imagen desplegada. Se omiten OPTIONS/HEAD implícitos y /admin/. Los permisos declarados no sustituyen las reglas por operación y por objeto.

Hay 59 patrones API/documentación. OpenAPI 3.1.0 publica 10 paths del recorrido base bajo /api/v1; no representa los módulos ampliados como si estuvieran versionados.

| Métodos | Ruta Django | Vista | Permiso declarado |
| --- | --- | --- | --- |
| GET | `/api/openapi.json` | schema | Función de documentación pública |
| GET | `/api/docs/` | swagger_ui | Función de documentación pública |
| GET | `/api/docs/live.js` | live_script | Función de documentación pública |
| GET | `/api/v1/auth/csrf/` | CsrfView | AllowAny |
| POST | `/api/v1/auth/login/` | LoginView | AllowAny |
| GET | `/api/v1/auth/me/` | MeView | CanAccessSession |
| POST | `/api/v1/auth/logout/` | LogoutView | CanAccessSession |
| GET, POST | `/api/v1/assets/` | AssetsView | IsManager |
| GET | `/api/v1/assets/<int:asset_id>/` | AssetView | IsManager |
| GET | `/api/v1/assets/<int:asset_id>/movements/` | MovementsView | IsManager |
| POST | `/api/v1/assets/<int:asset_id>/deliver/` | OperationView | IsManager |
| POST | `/api/v1/assets/<int:asset_id>/return/` | OperationView | IsManager |
| GET, POST | `/api/v1/custodians/` | CustodiansView | IsManager |
| POST | `/api/auth/change-password/` | ReviewerPasswordView | IsAuthenticated |
| POST | `/api/assets/<int:asset_id>/retire/` | RetireView | IsAuthenticated |
| GET, POST | `/api/assets/<int:asset_id>/retirement-requests/` | RetirementRequestsView | IsAuthenticated |
| GET | `/api/reviewer/retirement-requests/` | AssignedRequestsView | IsAssignedReviewer |
| POST | `/api/retirement-requests/<int:request_id>/decision/` | DecisionView | IsAssignedReviewer |
| POST | `/api/retirement-requests/<int:request_id>/reassign/` | ReassignView | IsAuthenticated |
| GET, POST | `/api/operator/reviewers/` | ReviewersView | IsAuthenticated |
| PATCH | `/api/operator/reviewers/<int:user_id>/` | ReviewerView | IsAuthenticated |
| GET | `/api/auth/csrf/` | CsrfView | AllowAny |
| POST | `/api/auth/login/` | LoginView | AllowAny |
| GET | `/api/auth/me/` | MeView | CanAccessSession |
| POST | `/api/auth/logout/` | LogoutView | CanAccessSession |
| GET, POST | `/api/license-lots/` | LicenseLotsView | IsManager |
| GET, PATCH | `/api/license-lots/<int:lot_id>/` | LicenseLotView | IsManager |
| GET | `/api/license-lots/<int:lot_id>/history/` | LicenseLotHistoryView | IsManager |
| GET, POST | `/api/assets/` | AssetsView | IsManager |
| GET, PATCH | `/api/assets/<int:asset_id>/` | AssetView | IsManager |
| GET | `/api/assets/by-code/<str:code>/` | AssetByCodeView | IsManager |
| GET | `/api/assets/<int:asset_id>/qr.svg` | AssetQrView | IsManager |
| GET | `/api/assets/<int:asset_id>/movements/` | MovementsView | IsManager |
| GET, POST | `/api/assets/<int:asset_id>/incidents/` | IncidentsView | IsManager |
| POST | `/api/assets/<int:asset_id>/recover/` | AssetRecoveryView | IsManager |
| POST | `/api/incidents/<int:incident_id>/resolve/` | IncidentResolutionView | IsManager |
| GET | `/api/maintenance/<int:maintenance_id>/` | MaintenanceDetailView | IsManager |
| POST | `/api/assets/<int:asset_id>/maintenance/` | MaintenanceStartView | IsManager |
| POST | `/api/maintenance/<int:maintenance_id>/close/` | MaintenanceCloseView | IsManager |
| GET, POST | `/api/custodians/` | CustodiansView | IsManager |
| GET | `/api/options/` | OptionsView | IsManager |
| GET | `/api/faculties/` | FacultiesView | IsManagerOrOperator |
| GET, POST | `/api/operator/faculties/` | OperatorFacultiesView | IsOperator |
| PATCH | `/api/operator/faculties/<int:faculty_id>/` | OperatorFacultyView | IsOperator |
| PATCH | `/api/operator/assets/<int:asset_id>/faculty/` | OperatorAssetFacultyView | IsOperator |
| POST | `/api/acquisitions/` | AcquisitionsView | IsManager |
| GET, PATCH | `/api/acquisitions/<int:document_id>/` | AcquisitionView | IsManager |
| PATCH | `/api/custodians/<int:custodian_id>/` | CustodianView | IsManager |
| GET | `/api/assets/<int:asset_id>/history/` | AssetHistoryView | IsManager |
| GET | `/api/imports/templates/<str:kind>/` | TemplatesView | IsManager |
| POST | `/api/imports/previews/` | PreviewsView | IsManager |
| GET | `/api/imports/<uuid:batch_id>/` | BatchView | IsManager |
| POST | `/api/imports/<uuid:batch_id>/confirm/` | ConfirmView | IsManager |
| POST | `/api/imports/<uuid:batch_id>/apply/` | ApplyView | IsManager |
| POST | `/api/imports/<uuid:batch_id>/cancel/` | CancelView | IsManager |
| POST | `/api/assets/<int:asset_id>/deliver/` | OperationView | IsManager |
| POST | `/api/assets/<int:asset_id>/return/` | OperationView | IsManager |
| POST | `/api/assets/<int:asset_id>/condition/` | OperationView | IsManager |
| POST | `/api/assets/<int:asset_id>/rectify/` | OperationView | IsManager |

## Contratos canónicos por módulo

- [002-registro-consulta-activos/api.md](../../specs/002-registro-consulta-activos/contracts/api.md).
- [002-registro-consulta-activos/web.md](../../specs/002-registro-consulta-activos/contracts/web.md).
- [003-fichas-adquisiciones/api.md](../../specs/003-fichas-adquisiciones/contracts/api.md).
- [003-fichas-adquisiciones/web.md](../../specs/003-fichas-adquisiciones/contracts/web.md).
- [004-novedades-mantenimiento/api.md](../../specs/004-novedades-mantenimiento/contracts/api.md).
- [004-novedades-mantenimiento/web.md](../../specs/004-novedades-mantenimiento/contracts/web.md).
- [005-bajas-aprobacion/api.md](../../specs/005-bajas-aprobacion/contracts/api.md).
- [005-bajas-aprobacion/web.md](../../specs/005-bajas-aprobacion/contracts/web.md).
- [006-lotes-licencias/api.md](../../specs/006-lotes-licencias/contracts/api.md).
- [006-lotes-licencias/web.md](../../specs/006-lotes-licencias/contracts/web.md).
- [007-qr-activos/api.md](../../specs/007-qr-activos/contracts/api.md).
- [007-qr-activos/web.md](../../specs/007-qr-activos/contracts/web.md).
- [008-importacion-csv/api.md](../../specs/008-importacion-csv/contracts/api.md).
- [008-importacion-csv/web.md](../../specs/008-importacion-csv/contracts/web.md).

Las pruebas de /api/v1/ validan el sobre success/message/data/errors/meta. Los módulos bajo /api/ conservan su formato histórico; los clientes deben usar el contrato de la ruta concreta. Las fechas se transmiten en formatos ISO documentados y los valores monetarios como decimales de precisión controlada, no floats binarios.
