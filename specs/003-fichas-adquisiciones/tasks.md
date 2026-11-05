# Tareas: fichas y adquisición

**Estado vigente (2026-11-04):** 11 tareas completas y 7 parciales. El cierre autónomo, sus evidencias y bloqueos están al final; los apartados anteriores conservan el historial real de ejecución. Ninguna integración ausente se considera validada.

## Fase 1 — Fundamentos

- [X] T001 Añadir casos API y de servicio para documentos de compra/donación, importes compartidos, fecha desconocida y restricciones de edición en backend/inventory/tests/test_acquisitions.py.
- [X] T002 Añadir pruebas de sesión/provisión local de Operador, permisos para administración de facultades y edición de ficha en backend/inventory/tests/test_permissions.py.
- [X] T003 Crear Faculty, AcquisitionDocument, AcquisitionLine y modelos de auditoría en backend/inventory/models.py.
- [ ] T004 Obtener y completar manualmente con el grupo el mapeo de facultad responsable para cada activo existente; detener la migración si faltan datos verificados. Crear migración compatible, sin completar origen/facultad por suposición, en backend/inventory/migrations/.
- [ ] T005 Implementar validaciones condicionales de compra/donación y fecha desconocida en backend/inventory/serializers.py.
- [X] T006 Implementar alta atómica de activo+línea con documento existente, revisión global y servicios atómicos de adquisición y actualización auditada en backend/inventory/services.py.
- [ ] T007 Implementar create_operator y permisos/sesión de Operador en management/commands/, permissions.py y auth_views.py; añadir rutas y vistas protegidas para facultades, adquisición, edición y auditoría en backend/inventory/urls.py y backend/inventory/views.py.

## US1 — Compra compartida

- [X] T008 [US1] Implementar creación/lectura de factura y líneas por activo; total compartido y valor individual en backend/inventory/services.py.
- [X] T009 [US1] Implementar formularios web de compra y enlace de múltiples activos en frontend/src/components/AcquisitionForm.tsx.
- [X] T010 [US1] Probar compra con varios activos, campos requeridos, importes y error transaccional en backend/inventory/tests/test_acquisitions.py y frontend/src/tests/acquisition.test.tsx.

## US2 — Donación compartida

- [ ] T011 [US2] Implementar respaldo textual compartido y valor por activo en backend/inventory/serializers.py y backend/inventory/services.py.
- [X] T012 [US2] Implementar captura web de donación y valores estimados individuales en frontend/src/components/AcquisitionForm.tsx.
- [X] T013 [US2] Probar respaldo compartido, valores separados y rechazo de campos de factura no aplicables en backend/inventory/tests/test_acquisitions.py.

## US3 — Edición y facultades

- [X] T014 [US3] Implementar PATCH auditado de activo y custodio preservando snapshots en backend/inventory/services.py.
- [ ] T015 [US3] Implementar administración de facultades para operador y selector de facultad en frontend/src/components/FacultyManagement.tsx y frontend/src/components/Registration.tsx.
- [ ] T016 [US3] Implementar vistas web de edición y cambios históricos en frontend/src/components/AssetEditForm.tsx y frontend/src/components/History.tsx.
- [ ] T017 [US3] Probar identidad duplicada al editar, campos de estado reservados, auditoría y permisos en backend/inventory/tests/test_assets.py y frontend/src/tests/asset-edit.test.tsx.
- [X] T018 Actualizar contratos, README y quickstart tras validación en specs/003-fichas-adquisiciones/ y README.md.

## Dependencias

T001–T007 bloquean historias. US1 y US2 dependen de entidades/servicios; US3 depende de Faculty y auditorías. Los tests corren en PostgreSQL y frontend existente. El estado vigente es el de las casillas y las últimas secciones de evidencia; los informes anteriores son históricos.
## Trazabilidad FR → tareas

- FR-001: T003, T005, T014
- FR-002: T001, T006, T014, T017
- FR-003: T014, T017
- FR-004: T005, T014, T017
- FR-005: T002, T003, T007, T015
- FR-006: T003, T004, T015
- FR-007–FR-012: T001, T003–T013
- FR-013: T001, T003, T005, T006, T014, T017
- FR-014: T001, T005, T017
- FR-015: T003, T004, T006, T017
- FR-016: T002, T003, T006, T007, T015, T017

## Evidencia del bloque inicial — 2026-11-04

T001, T002 y T003 siguen parciales y sin marcar: pruebas rojas y modelos preparados, con límites y cobertura pendiente en [implementation.md](implementation.md) y ejecución real en [validation.md](validation.md). T004 no implementada; su estrategia debe abortar si falta mapeo histórico verificado. No se aplicaron migraciones a la base local.

## Correcciones técnicas tras auditoría — 2026-11-04

T001–T003 continúan parciales, sin marcar [x]. Evidencia final: selección de regresión 65/65 backend; aceptación pendiente 14 métodos, failures=17 por subtests, errors=0; frontend 20/20 y build PASS. Ver validation.md para comandos y límites. No se generaron migraciones.

## Primera parte T004 — 2026-11-04

Expansión preparada en 0004_acquisition_expansion, aplicada solo en PostgreSQL temporal: diez pruebas de expansión PASS y regresión seleccionada 75/75. T004 conserva [ ]: faltan mapeo verificado, completado autorizado, validación de CHECK legados y NOT NULL de facultad después de adaptar altas. Aceptación 003 sigue pendiente (14 métodos; 15 fallos por subtests y un error de servicio T006). No se modificó la base local.

## Inicio T005/T006 — 2026-11-04

Validaciones y primitivas transaccionales implementadas parcialmente: documento de metadatos, alta activo+línea, asociación, actualización auditada base y guarda de revisión global. Selección verde 92/92; aceptación API/Operador 13 métodos, failures=15 por subtests, errors=0. T005/T006 conservan [ ] por decisiones y edición documental compartida pendientes; no se implementaron T007–T018 ni se aplicaron migraciones locales. Evidencia exacta en validation.md.

## T007 — 2026-11-04

Provisión Operador, sesión/roles, catálogo y rutas de adquisición/alta/edición de activo/historia implementados en el alcance aprobado. Backend completo 118/118, frontend 20/20 y build PASS; doce métodos antes rojos se convirtieron a verde, uno ya pasaba. T007 conserva [ ]: cambio de facultad depende de 005, edición documental/custodio y orquestación de items siguen bloqueados sin éxito ficticio. T001–T006 también conservan sus estados parciales por los pendientes detallados en implementation.md. Sin migración local, commits ni avance a T008–T018.


## T008–T010 — compras, 2026-11-04

Flujo factura-primero para activos nuevos implementado en React y probado: crear/cargar factura, reutilizarla en varias altas atómicas, valores individuales, facultad, fecha/motivo, sesión/CSRF y errores junto a campos. Reutiliza los servicios existentes; lectura añade asset_code readonly y no crea ni altera registros. Nuevos PurchaseFlowTests (6) y acquisition.test.tsx (14).

Resultado final: backend completo 124/124; frontend completo 34/34; build PASS. Se conservan T008/T009/T010 [ ] para el cierre integral del camino contractual de items iniciales sobre activos existentes, aún no orquestado con fecha/revisión/motivo definidos. El flujo nuevo ya funciona y no depende de esa rama. No se añaden políticas ni se completa T001–T007 por esos resultados. Ver implementation.md y validation.md.

## Cierre T008–T010 tras confirmación humana — 2026-11-04

Este estado sustituye el informe anterior de compras: T008 completa creación/lectura y asociaciones iniciales atómicas de activos existentes, además del alta posterior de activos nuevos. T009 completa formulario React con factura compartida, lista de asociaciones existentes con revisión/motivo/fecha y registro de activos nuevos con importes propios. T010 completa cobertura del alcance aprobado: varios activos, campos requeridos, importes individuales, duplicados, revisión, concurrencia y rollback real. Evidencia final: 134/134 backend en PostgreSQL temporal, 37/37 frontend y build correcto. Las pruebas cubren API y servicios reales; frontend usa HTTP simulado únicamente en tests. No es evidencia de cierre de T001–T007 ni de decisiones monetarias/donaciones pendientes; no se avanzó T011–T018.

## Donaciones T011–T013 — 2026-11-04

T011 conserva [ ] como parcial: caminos aprobados de documento/alta/asociación implementados reutilizando adquisición; cierre integral condicionado a reglas monetarias y fecha documental pendientes. La asociación inicial fue confirmada por Alex para estimated_value + revisión/motivo/fecha, sin adquisición vigente y transacción global. T012 [X]: formulario compartido React, navegación, tipo/referencia, valores estimados, fechas, asociaciones, errores y conservación de datos. T013 [X]: casos de respaldo compartido, valores separados y campos de factura rechazados, más integridad, concurrencia, rollback, permisos y CSRF. No se considera aprobada ninguna política pendiente por el resultado verde; su límite explícito también se prueba. Ver validation.md para resultados reales. T014–T018 sin iniciar.

## Estado vigente T014–T017 — 2026-11-04

T014 [X]: PATCH descriptivo/de línea de activo reutilizado y custodio auditado real, con contrato reason/expected_profile expresamente confirmado por Alex. Snapshots, actor/fecha, conflictos, rollback e inmutabilidad comprobados; sin reescribir movimientos ni aumentar revisiones de activos por editar custodio. No incluye desbloquear PATCH documental compartido.

T015 [ ] parcial: catálogo Operador activo/inactivo, creación/edición y selector inicial disponibles; servicio de cambio de facultad y auditoría preparados, pero guardia 005 real ausente y 503 seguro. T016 [ ] parcial: edición React de activo/custodio, diferencias confirmables e historial combinado disponibles; cambio posterior de facultad permanece bloqueado en UI por 005. T017 [ ] parcial: requisitos aislados pasan, pero aceptación con proveedor real 005 pendiente, sin simular su existencia.

Evidencia final: backend completo 162/162 en PostgreSQL temporal; frontend 53/53; compilación correcta; git diff --check sin errores. T001–T007, T004 y T011 conservan pendientes anteriores. T018 sin iniciar. Ver implementation.md, validation.md e integration-notes.md para archivos, comandos, fallos intermedios corregidos y límites.

## Cierre autónomo vigente T001–T018 — 2026-11-04

| Tarea | Estado | Evidencia o pendiente |
|---|---|---|
| T001 | Completa | Casos API/servicios de adquisición, edición, fecha/motivo, rollback y límites explícitos. |
| T002 | Completa | Provisión/sesión Operador, CSRF, separación de roles y denegaciones verificadas. |
| T003 | Completa | Siete entidades, relaciones, constraints y conservación ORM/SQL probados; 0004 preparada. |
| T004 | Parcial | Expansión y preflight sin escrituras; plantilla de contracción probada fuera del grafo activo. Falta mapeo/revisión de escritores antes de NOT NULL. |
| T005 | Parcial | Reglas aprobadas implementadas; cero/negativos y fecha documental de donación siguen pending_decision. |
| T006 | Completa | Alta/asociación/edición, PATCH documental confirmado e import_assets reales, transaccionales y auditados. |
| T007 | Parcial | Sesión, roles, rutas y servicios reales disponibles; cambio de facultad sigue 503 por proveedor 005 ausente. |
| T008 | Completa | Compra compartida, activos nuevos/existentes y valores individuales. |
| T009 | Completa | Formularios de compra y consulta/reutilización del documento. |
| T010 | Completa | Regresión y aceptación de compras con integridad/concurrencia. |
| T011 | Parcial | Donaciones manuales/documento existente operativas; nuevas desde CSV permanecen bloqueadas por decisión expresa, además de políticas abiertas. |
| T012 | Completa | Interfaz de donaciones del alcance aprobado. |
| T013 | Completa | Respaldo compartido, valores, campos no aplicables y límites probados. |
| T014 | Completa | Edición auditada de activo/custodio preservando historia. |
| T015 | Parcial | Catálogo y selectores completos; cambio posterior de facultad requiere integración real 005. |
| T016 | Parcial | Edición de activos/custodios/documentos e historial completa; UI de cambio de facultad bloqueada por 005. |
| T017 | Parcial | Pruebas aisladas y regresión pasan; escenarios con proveedor real 005 pendientes. |
| T018 | Completa | SDD/README/quickstart, inventario y pr-description preparados con límites y evidencia; PR no publicado. |

Validación final: 182/182 backend, 57/57 frontend, build correcto, check sin incidencias, makemigrations --check --dry-run sin cambios, pip check correcto, diff --check sin errores. La suite backend incluye expansión, plantilla de contracción, integridad, carreras y gateway 008 de producción. Solo PostgreSQL temporal; ninguna migración local.
