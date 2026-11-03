# Validación: importación CSV (008)

**Fecha:** 2026-11-02
**Versiones:** Python 3.13.14, Django 5.2.18, PostgreSQL 17, Node 24.18.0, npm 11.16.0.
**Alcance:** pruebas automáticas ejecutadas. La integración real con 003/006 y la aceptación manual están pendientes.

## Resumen

| Suite | Comando exacto (raíz del repo) | Resultado |
| --- | --- | --- |
| Dominio aislado | `backend\.venv\Scripts\python.exe -m unittest discover -s backend\inventory\isolated_tests\imports -p "test_*.py"` | PASS, 16 pruebas |
| API/DB PostgreSQL efímero | `backend\.venv\Scripts\python.exe backend\tools\test_postgres.py` | PASS, 45 pruebas |
| Frontend | `npm test -- --run` desde `frontend/` | PASS, 20 pruebas (8 archivos) |
| Build frontend | `npm run build` desde `frontend/` | PASS, `tsc --noEmit` y Vite |
| Migraciones | `manage.py makemigrations --check --dry-run` con PostgreSQL efímero | PASS, `No changes detected` |

Las pruebas API usan `inventory.tests.fake_import_gateway.FakeGateway` mediante `override_settings(IMPORT_GATEWAY=...)`. No son evidencia de integración real con 003/006.

## Casos de dominio (sin Django ni proveedores)

| Caso | Test | Resultado |
| --- | --- | --- |
| Ejemplo de activos versionado válido y resumen | `AssetParsingTests.test_ejemplo_versionado_es_valido` | PASS |
| Ejemplo de licencias versionado válido | `LicenseParsingTests.test_ejemplo_versionado_es_valido` | PASS |
| Hash estable ante BOM/espacios externos | `test_hash_es_estable_y_las_limpiezas_no_lo_cambian` | PASS |
| Cabecera faltante y columna extra | `test_cabecera_faltante_y_columna_extra` | PASS |
| Versión no soportada y archivo vacío | `test_version_no_soportada_y_archivo_vacio` | PASS |
| UTF-8 inválido y bytes nulos | `test_utf8_invalido_y_bytes_nulos` | PASS |
| Errores múltiples completos por fila | `test_errores_multiples_por_fila_se_listan_completos` | PASS |
| Límites de bytes y filas | `test_limites_de_bytes_y_filas` | PASS |
| Documento existente y `document_key` excluyentes | `test_documento_existente_y_key_son_excluyentes` | PASS |
| Documentos compartidos con metadatos iguales | `test_documentos_compartidos_exigen_metadatos_iguales` | PASS |
| Duplicado de identidad dentro del archivo | `test_duplicado_de_identidad_dentro_del_archivo` | PASS |
| Fecha y motivo desconocido alternativos | `test_fecha_y_motivo_desconocido_son_alternativas` | PASS |
| Líneas en blanco sin alterar numeración | `test_lineas_en_blanco_se_omiten_sin_alterar_numeracion` | PASS |
| Identificadores positivos | `test_identificadores_deben_ser_positivos` | PASS |
| Licencias: inicio obligatorio y cantidades | `LicenseParsingTests.test_inicio_obligatorio_y_cantidades` | PASS |
| Licencias: fin anterior al inicio/modelo inválido | `LicenseParsingTests.test_fin_anterior_al_inicio_y_modelo_invalido` | PASS |

## Casos API/DB/permisos (PostgreSQL efímero + fake de pruebas)

| Caso | Test | Resultado |
| --- | --- | --- |
| Plantilla descargable y tipo inválido | `ImportApiTests.test_plantilla_descargable` | PASS |
| Preview válido no escribe dominio | `test_preview_valido_no_escribe_dominio` | PASS |
| Preview inválido lista errores y no confirma | `test_preview_invalido_lista_errores_y_no_habilita_confirmacion` | PASS |
| Dos confirmaciones y reintento idempotente 200 | `test_ciclo_doble_confirmacion_y_reintento_idempotente` | PASS |
| Apply exige confirmación y hash vigente | `test_apply_requiere_confirmacion_y_hash_vigente` | PASS |
| Documentos compartidos por API | `test_documentos_compartidos_y_referencias` | PASS |
| Licencias válidas e inválidas por API | `test_licencias_validas_e_invalidas` | PASS |
| Revalidación al aplicar rechaza todo | `test_revalidacion_al_aplicar_rechaza_todo` | PASS |
| Fallo del proveedor revierte y permite reintentar | `test_fallo_del_proveedor_revierte_y_permite_reintentar` | PASS |
| Cancelación impide confirmar/aplicar | `test_cancelacion_impide_confirmar_y_aplicar` | PASS |
| Expiración elimina contenido temporal | `test_expiracion_elimina_contenido_temporal` | PASS |
| Otro gestor no consulta ni confirma | `test_otro_gestor_no_consulta_ni_confirma` | PASS |
| Límite de bytes → 413 | `test_limite_de_bytes` | PASS |
| Límite de filas → 413 | `test_limite_de_filas` | PASS |
| Paginación devuelve todas las filas | `test_get_pagina_todas_las_filas` | PASS |
| Carga multipart exige CSRF | `ImportCsrfTests.test_carga_multipart_exige_csrf` | PASS |
| Dos aplicaciones simultáneas crean una vez | `ImportConcurrencyTests.test_dos_aplicaciones_simultaneas_crean_una_vez` | PASS |

## Frontend

| Caso | Test | Resultado |
| --- | --- | --- |
| Plantilla del tipo elegido | `frontend/src/tests/import.test.tsx` (1) | PASS |
| Errores de archivo y confirmación deshabilitada | mismo archivo (2) | PASS |
| Dos confirmaciones con el mismo hash, apply y cierre | mismo archivo (3) | PASS |
| Compilación TypeScript y bundle | `npm run build` | PASS |

## No ejecutado / dependencia no integrada

- **NO EJECUTADO:** aceptación manual en navegador con 003/006 reales, incluyendo códigos TI, activos Disponibles sin custodio y licencias en base real.
- **DEPENDENCIA NO INTEGRADA:** modelos/servicios de 003 y 006 ausentes en `origin/develop`; el gateway de producción responde 503. La transacción real de dominio, unicidad concurrente y contratos de función no están verificados.
- **NO EJECUTADO:** prueba de cambio concurrente de facultad/documento/identidad durante la ventana de preview contra proveedores reales. La orquestación sí se probó con fake (`test_revalidacion_al_aplicar_rechaza_todo` y concurrencia de apply).
- **NO EJECUTADO:** retención de resultados durante 30 días (solo se verificó el valor configurado y la limpieza de contenido temporal).
