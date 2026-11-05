# Evidencia técnica de requisitos principales

Base: develop cbb632d. Las rutas apuntan al repositorio. Los identificadores HU corresponden al dossier de semana 2. Las pruebas indican comportamientos relacionados, no prueban necesariamente todos los detalles de cada requisito agrupado.

| Historia | Requisito | Prueba de referencia | Comportamiento |
| --- | --- | --- | --- |
| HU-01 | 002/FR-002, FR-015 | backend/inventory/tests/test_assets.py::test_creation_code_fields_and_stability | Código generado y datos del alta |
| HU-02 | 002/FR-012–FR-014 | backend/inventory/tests/test_custody.py | Entrega, devolución y custodia |
| HU-03 | 002/FR-016–FR-017 | backend/inventory/tests/test_rectification.py | Reglas de rectificación |
| HU-04 | 003/FR-008, FR-011 | backend/inventory/tests/test_acquisitions.py::test_several_assets_reuse_invoice_and_keep_exact_individual_values | Factura compartida y valores individuales |
| HU-05 | 004/FR-001–FR-004 | backend/inventory/tests/test_incidents.py::test_assigned_asset_report_and_resolution_preserve_custody_and_history | Novedad y resolución conservan custodia |
| HU-06 | 004/FR-007–FR-009 | backend/inventory/tests/test_maintenance.py::test_preventive_maintenance_blocks_delivery_and_closes_without_changing_condition | Bloqueo de entrega y condición separada |
| HU-07 | 004/FR-010–FR-013 | backend/inventory/tests/test_incidents.py::test_loss_during_maintenance_and_recovery_preserve_original_evidence | Pérdida en taller y recuperación |
| HU-08 | 005/FR-001–FR-004 | backend/inventory/tests/test_retirement_integration.py::test_normal_retirement_preserves_acquisition | Baja conserva adquisición |
| HU-09 | 005/FR-006, FR-008, FR-010 | backend/inventory/tests/test_retirement_integration.py::test_reviewer_approves_and_retirement_can_be_rectified; test_pending_request_blocks_faculty_change_and_cancels_on_recovery | Aprobación, rectificación y recuperación |
| HU-10 | 006/FR-003–FR-005 | backend/inventory/tests/test_license_lots.py::test_database_rejects_invalid_values_even_without_api | Rangos y restricciones de cantidades |
| HU-11 | 007/FR-001, FR-004, FR-006 | backend/inventory/test_qr_assets.py::test_qr_contiene_url_canonica_sin_datos_privados; test_sin_sesion_no_puede_descargar_ni_consultar | QR y acceso protegido |
| HU-12 | 008/FR-003, FR-005, FR-007 | backend/inventory/tests/test_imports.py::test_preview_invalido_lista_errores_y_no_habilita_confirmacion; test_ciclo_doble_confirmacion_y_reintento_idempotente; backend/inventory/tests/test_import_acquisitions.py::test_actual_second_line_sql_failure_reverts_entire_batch_and_document | Rechazo completo, confirmaciones y rollback |

En la revisión previa del commit cbb632d pasaron 307 pruebas de inventario y contrato. El recorrido integrado con base temporal comprendió sesión/CSRF, importación de compra, QR, mantenimiento, pérdida, solicitud de baja y recuperación con cancelación. Una prueba concreta solo acredita lo que comprueba su propio código. La importación de una nueva donación tiene un caso de bloqueo explícito en backend/inventory/tests/test_import_acquisitions.py::test_new_donation_csv_remains_explicitly_blocked_by_human_decision.
