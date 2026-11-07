# Implementación 003 — cierre documental vigente

Fecha de entrega: 2026-11-04 (America/Guayaquil). Rama Alex_Sigcho_Feature; PR previsto hacia develop. Consolidación reanudada tras interrupción; solo cambios documentales, sin rehacer funcionalidades ni modificar datos locales.

Hay 11 tareas COMPLETAS y 7 PARCIALES. Ninguna tarea completa queda declarada integralmente validada con un proveedor ausente; los bloqueos se detallan por alcance.

| Tarea | Estado | Evidencia / pendiente |
|---|---|---|
| T001 | COMPLETA | Pruebas API/servicios de adquisición, fechas, edición, rechazo y rollback. |
| T002 | COMPLETA | Provisión, sesión, CSRF y separación Gestor/Operador verificadas. |
| T003 | COMPLETA | Modelos, relaciones, constraints y auditorías ORM/SQL preparados y probados. |
| T004 | PARCIAL | Expansión y preflight listos; falta transición de legado revisada y NOT NULL activo. |
| T005 | PARCIAL | Reglas aprobadas implementadas; política monetaria y fecha documental de donación pendientes. |
| T006 | COMPLETA | Servicios atómicos de alta, asociación, edición, documento compartido e importación real. |
| T007 | PARCIAL | Rutas/sesión operativas; cambio posterior de facultad bloqueado por proveedor 005 ausente. |
| T008 | COMPLETA | Factura compartida y valores individuales de activos nuevos/existentes. |
| T009 | COMPLETA | Interfaz de compra y reutilización del documento. |
| T010 | COMPLETA | Aceptación y regresión de compras verificadas. |
| T011 | PARCIAL | Donaciones manuales y documento existente operativos; políticas abiertas y donación CSV nueva bloqueada. |
| T012 | COMPLETA | Interfaz de donaciones del alcance aprobado. |
| T013 | COMPLETA | Respaldo compartido, valores separados, campos no aplicables y límites probados. |
| T014 | COMPLETA | Edición auditada de activos/custodios sin reescribir movimientos. |
| T015 | PARCIAL | Catálogo y selectores listos; cambio posterior requiere guardia real 005. |
| T016 | PARCIAL | Edición e historial integrados; UI de cambio de facultad bloqueada por 005. |
| T017 | PARCIAL | Regresión y pruebas aisladas pasan; aceptación con proveedor real 005 pendiente. |
| T018 | COMPLETA | SDD, README, quickstart, inventario y cuerpo de PR preparados; sin publicación. |

## Implementado y verificado

- Modelos de facultades, documentos/líneas y evidencia append-only; expansión 0004 con protección PostgreSQL y compatibilidad de legado.
- Operador por create_operator, sesión/CSRF y permisos separados. Catálogo activo/inactivo y selección inicial de facultad.
- Compras y donaciones manuales: respaldo compartido, valor individual, USD persistido y fecha o motivo; altas y asociaciones atómicas con revisión/auditoría.
- Edición de activo/custodio e historial combinado preservando movimientos y snapshots. Custodios usan el contrato confirmado reason + expected_profile.
- PATCH documental con reason, expected_document completo y expected_revisions de todos los activos; lock documento → activos por id, revisión de pertenencia, auditoría documental y AssetChange por activo en una transacción. Documentos vacíos también protegidos.
- import_assets real consumido por gateway de producción 008: agrupación por clave local del lote, reutilización de documentos existentes, rollback y aplicación idempotente de ImportBatch.
- Formularios React con diferencias confirmables, conservación de borradores, errores visibles y ausencia de reintentos automáticos. Cuentas con ambos permisos explícitos pueden navegar al catálogo sin conceder Gestor a un Operador.
- Diagnóstico acquisition_preflight de solo lectura y plantilla faculty_contract.py.txt fuera del grafo activo; pruebas de aborto con legado incompleto y contracción con mapeo verificado.

## Validación y problemas corregidos

Última validación funcional registrada: 182/182 backend, 57/57 frontend y build correcto. check y makemigrations --check --dry-run ejecutados mediante el runner aislado; sin incidencias ni cambios. pip check y diff --check correctos.

Se corrigió el envío interno de support_type vacío al crear compras CSV, sin relajar la validación estricta; se actualizó el rechazo documental incompleto a 400 conforme al contrato confirmado. La prueba de contracción verifica las FK diferidas antes del DDL, sin desactivarlas. Las carreras reales cubren documento vacío, edición frente a asociación y aplicación concurrente del mismo lote CSV.

La reanudación inspeccionó 94 archivos funcionales: ninguno tiene modificación posterior al inicio de la última validación registrada. No se introdujeron cambios funcionales ni se repitieron suites innecesariamente. Esta comprobación de continuidad por archivos no se presenta como una nueva ejecución de pruebas.

## Pendientes

- T004: Asset.faculty sigue nullable en el grafo activo. El dato de 0 activos locales fue aportado por Alex, no se consultó de nuevo ni se aplicaron migraciones a esa base. Para cualquier instalación se requiere inventario/mapeo de facultad verificado, resolución de textos incompatibles, revisión de todos los escritores (incluidos consumidores 002), VALIDATE de CHECK legados y promoción revisada de la contracción. No se inventan adquisiciones ni facultades.
- Decisiones humanas: importes cero/negativos y fecha documental de donación continúan con rechazo explícito pending_decision. Cambiar origen compra/donación no está habilitado. Alex indicó mantener bloqueada la donación nueva desde CSV; no se infiere support_type de support_description.
- 005: ensure_no_pending_decommission falla cerrada con 503 mientras falte el proveedor real. Cambio de facultad permitido/pendiente/concurrente está probado solo con sustitutos de esa guardia en tests, no con 005 real.
- 008: integración real verificada para compras nuevas por document_key y documentos existentes, incluida donación con documento existente. Creación de donación nueva por CSV no integrada por decisión expresa. El proveedor de licencias 006 queda fuera de 003.
- Revisión humana de entrega y despliegue pendientes. Constitución continúa propuesta; no se atribuye ratificación al equipo.


## Archivos y revisión

El inventario completo del árbol de trabajo está en [file-inventory.md](file-inventory.md); incluye código previo conservado y documentación de esta reanudación. El detalle de comandos/resultados está en [validation.md](validation.md). El cuerpo revisable de PR está en [pr-description.md](pr-description.md). No se hicieron commits, push ni PR.

Trabajo asistido por IA. Confirmaciones humanas recibidas para payloads de asociación, protocolo de custodios y protocolo documental; la donación CSV nueva permanece bloqueada expresamente. El código sigue pendiente de revisión por otro integrante.


<details>
<summary>Historial de bloques anteriores — sus estados no sustituyen el cierre vigente</summary>

# Implementación parcial 003 — compras T008–T010, 2026-11-04

Las secciones T007 conservan evidencia del bloque anterior; el estado vigente de compras está al final.

Rama verificada: Alex_Sigcho_Feature. Destino futuro: develop. Se conservaron los cambios de T001–T006 y 0004; no se generaron/aplicaron migraciones nuevas ni se modificaron .env o datos locales. Sin commits, push ni PR. Trabajo asistido por Codex; revisión humana pendiente.

## Archivos de T007

| Archivo | Cambio real y requisito |
|---|---|
| backend/inventory/management/commands/create_operator.py (nuevo) | Provisión local interactiva según patrón create_gestor: full_clean, contraseñas coincidentes, validación Django y transacción. Solo añade Operadores; sin Gestores/staff/superuser. Cuenta existente y contraseña débil rechazadas sin cambios. FR-005/016 y contrato transversal. |
| backend/inventory/permissions.py | IsOperator y IsManagerOrOperator; default global IsManager conservado. session_payload con permissions explícitos y must_change_password=false para 003. El login no añade grupos ni permisos. |
| backend/inventory/auth_views.py | Login/me/logout reconocen Gestor/Operador activos. CSRF intacto, 403 por acceso/rol/inactivo con credenciales válidas, 400 por credenciales inválidas. Intento rechazado con CSRF válido limpia sesión previa. No hay Revisor/cambio inicial de contraseña de 005. |
| backend/inventory/faculty_services.py (nuevo) | Catálogo manual solo Operador, validación estricta y transacciones; identidad estable y unicidad normalizada PostgreSQL. Corrección no borra referencias; PATCH no reactiva por default una facultad inactiva. |
| backend/inventory/serializers.py | Salidas de facultad/documento/línea; AssetOutput añade faculty_id y adquisición/currency histórica. Validación del catálogo reutiliza StrictSerializer. |
| backend/inventory/views.py | Conecta servicios reales de T005/T006 para alta de documento sin items iniciales, alta completa y PATCH auditado de activo. Catálogo, lectura de documento e historial combinado. Rutas pendientes devuelven 409/503 sin escribir, no éxito ficticio. |
| backend/inventory/urls.py | Registra las rutas 003 declaradas; no cambia las rutas de importación ni paquetes 005/006/008. |
| backend/inventory/errors.py | DependencyUnavailable HTTP 503 con code dependency_unavailable para una operación cuyo proveedor/servicio aún no está disponible. |
| backend/inventory/tests/test_operator_api.py (nuevo) | 13 métodos: sesión/roles/CSRF, catálogo, duplicados/rollback, histórico, errores, bloqueos de dependencias, provisión duplicada y contraseña débil. |
| backend/inventory/tests/base.py | Fixture API completa de 003 creada bajo demanda. asset_data antiguo se conserva para servicios/legado 002. No datos de catálogo en producción ni ids supuestos. |
| backend/inventory/tests/test_assets.py | Adapta cuerpos API antiguos a los campos obligatorios aprobados de 003. Mantiene pruebas de códigos/duplicados/custodia/CSRF. PUT/DELETE siguen 405; PATCH vacío ahora exige reason/expected_revision, 400 y revisión intacta. No se eliminan métodos ni se relajan las reglas. |

Documentación actualizada: implementation.md, validation.md, integration-notes.md, tasks.md, contracts/api.md y quickstart.md.

## Endpoints y alcance vigente

| Ruta | Actor y resultado real |
|---|---|
| auth/login, auth/me, auth/logout | Gestor u Operador activo; sesión extendida y CSRF en mutaciones. |
| GET /api/faculties/ | Gestor/Operador: solo facultades activas. |
| POST /api/operator/faculties/ | Operador: 201; duplicado 409; inválido 400. |
| PATCH /api/operator/faculties/{id}/ | Operador: 200 con id/referencias conservados; DELETE no expuesto. |
| POST /api/acquisitions/ | Gestor: 201 solo metadatos, items omitido/vacío. Items no vacíos: 503, no crea documento. |
| GET /api/acquisitions/{id}/ | Gestor: documento real, currency persistida y líneas/valores individuales. |
| POST /api/assets/ | Gestor: 201 activo+línea atómicos. Exige campos base + faculty_id/acquisition_document_id/item_value/fecha o motivo; no acepta alta incompleta de 002 en esta API. |
| PATCH /api/assets/{id}/ | Gestor: primitiva auditada real de T006, reason y expected_revision; estados/facultad reservados. |
| GET /api/assets/{id}/history/ | Gestor: movimientos y auditorías 003 reales, revisión descendente; no modifica /movements/. |
| PATCH /api/operator/assets/{id}/faculty/ | Operador: 503 dependency_unavailable mientras falte la protección real de solicitudes 005; no cambia facultad/revisión. |
| PATCH /api/acquisitions/{id}/ | Gestor: 409 pending_decision; edición compartida no implementada ni habilitada. |
| PATCH /api/custodians/{id}/ | Gestor: 503 mientras falte el servicio auditado de perfil; no modifica custodios ni snapshots. |

Permisos de sesión técnicos: Gestores → inventory.manage; Operadores → faculties.manage. Una cuenta con ambos grupos explícitos tiene ambos scopes; iniciar sesión no concede uno por el otro. El alta create_operator solo crea Operadores. La autorización de cada endpoint usa grupos activos en backend, no el array enviado al cliente.

## Estado T001–T007 para revisión

| Tarea | Estado | Pendiente real |
|---|---|---|
| T001 | Parcial | Casos existentes API/servicio pasan; falta cobertura de edición documental compartida aún no implementada. |
| T002 | Parcial | Sesión/provisión/catálogo/separación de roles verdes; cambio efectivo de facultad depende de 005. |
| T003 | Parcial | Modelo y esquema preparados/probados temporalmente; revisión final contra las decisiones funcionales abiertas pendiente. |
| T004 | Parcial | Sin mapeo/completado verificado del legado, VALIDATE de CHECK NOT VALID ni faculty NOT NULL; no aplicada localmente. |
| T005 | Parcial | Validación aprobada disponible; dinero cero/negativo, fecha documental de donación y edición/origen documental siguen pendientes. |
| T006 | Parcial | Altas/asociación/edición base, revisión y rollback probados; faltan edición documental, concurrencia compartida completa e import_assets real. |
| T007 | Parcial | Provisión/sesión y rutas disponibles probadas; falta habilitar cambios de facultad con 005, PATCH documental, edición de custodio y orquestación de items iniciales con servicios reales. |

En el bloque T007 no se implementó frontend; esa situación histórica se actualiza con el flujo de compras descrito abajo. La administración de Operador y donaciones siguen pendientes; no se atribuye al test/build una validación manual de navegador. No se amplió el alcance funcional de 005/006/008. Cero/negativos y fecha documental explícita en donación siguen pending_decision sin escribir; no se decidió una política por inferencia.

## Evidencia del bloque T007

Suite backend completa: 118/118 PASS; frontend 20/20 y build PASS. Los 13 métodos anteriores de aceptación API/Operador pasan: 12 se convirtieron de rojo a verde y uno ya pasaba por la protección Gestor existente. Ningún test backend actual queda fallando; eso no acredita las operaciones explícitamente bloqueadas. Comandos, fallos intermedios y lista nominal en validation.md.

Skill speckit-implement: selección explícita/no persistente devuelve 003. Checklist requirements.md 10/10, sin modificar. Sin extensions.yml ni hooks antes/después. Ignore existente protege secretos/venv/node_modules/resultados. Constitución propuesta, sin atribuir ratificación. Revisión humana y autorización de migración local siguen pendientes.


## Compras T008–T010 — estado vigente del bloque autorizado

Rama Alex_Sigcho_Feature, sin cambios de rama ni descarte de trabajo anterior. Sin migraciones nuevas/locales, .env, datos locales, commits, push o PR. Destino futuro develop. Se leyeron tareas exactas, contratos API/web, plan y guía alex.md. Prerrequisitos 003 y checklist 10/10, sin hooks.

### Archivos de este bloque y trazabilidad

| Archivo | Cambio real y requisito |
|---|---|
| frontend/src/components/AcquisitionForm.tsx (nuevo) | Formulario de compra: crear factura textual o cargar por identificador existente; después reutiliza AssetForm para cada activo. Documento común conservado, valores individuales, facultad existente y fecha/motivo por activo. Solo éxito confirmado añade fila/código; error conserva datos/factura. FR-006/008/010–012; T009. |
| frontend/src/components/Registration.tsx | Reutiliza los campos base 002, añade contexto de compra (facultad/importe/fecha) sin duplicarlos. Sin selector de moneda, sin donaciones ni mantenimiento de catálogo. El selector mínimo es necesario para comprar, no completa T015. |
| frontend/src/App.tsx | Integra el flujo en Registrar activo, conserva formulario/locks al cerrar y reabrir dentro de la sesión, resetea por usuario y muestra ficha tras crear. Usa permissions reales; Operador sin inventory.manage no carga inventario/compras. Navegación de custodios/importación/operaciones conservada. |
| frontend/src/api.ts y types.ts | Métodos tipados sobre el transporte existente con sesión y CSRF; importes string, ids numéricos. Tipos de factura/líneas/facultad/sesión y snapshot; validación mínima de confirmación de respuestas, sin éxitos ficticios por JSON incompleto. |
| frontend/src/components/Form.tsx | Bloqueo de envío con ref y estados disabled; errores junto a campos con aria-invalid/describedby además del resumen. Nuevos nombres legibles de campos. Regresión de formularios/CSRF existente conservada. |
| frontend/src/components/Inventory.tsx y styles.css | Ficha readonly de compra distingue factura/total compartido/importe individual/fecha e identificador de documento. Estilos de error/resumen/checkbox y panel oculto; no edición T016. |
| backend/inventory/acquisition_services.py | Añade get_document autorizado de solo lectura y prefetch de activos en líneas; reutiliza los servicios existentes de alta/factura. No cambia política funcional ni duplica creación. T008, FR-008/011/012. |
| backend/inventory/views.py y serializers.py | GET documental delega al servicio real; salida de línea añade asset_code readonly para identificar el equipo en UI. Se conserva asset_id/item_value y total único en documento, sin total duplicado en líneas. |
| backend/inventory/tests/test_acquisitions.py | Seis casos PurchaseFlowTests: una compra, varios valores exactos, rechazos sin activo/línea parcial, UNIQUE real tras INSERT con rollback, segunda alta fallida preservando primera, lecturas sin revisión/auditoría nuevas. |
| frontend/src/tests/acquisition.test.tsx (nuevo) | 14 pruebas: flujo uno/varios activos, misma factura, error por campo, factura existente, navegación/guardado en curso, App/ficha, rol, datos inválidos, sin facultades, respuesta incierta y ausencia de reenvío/duplicación automáticos. HTTP simulado explícitamente; no navegador contra DB local. |

Documentación actualizada: implementation.md, validation.md, integration-notes.md, tasks.md, plan.md y quickstart.md. No se modifican funcionalidades exclusivas de otros paquetes ni se avanza a T011–T018.

### Secuencia, confirmación y atomicidad

Factura primero, mediante POST /acquisitions sin items; después cada POST /assets crea activo+línea atómicamente sobre ese documento existente. Se pueden registrar muchos activos repitiendo el segundo paso. No se inventa una transacción de lote: si el segundo falla, la factura y el primero confirmado se conservan. No se borran documentos vacíos ni se fabrica éxito. El total común no se iguala por obligación a la suma de líneas; las fechas de adquisición no se copian automáticamente de la factura.

La factura seleccionada y el lock de envío permanecen al cerrar/reabrir el panel dentro de la misma sesión; logout/expiración elimina ese estado privado. Los resultados añadidos se basan en la respuesta confirmada y los campos se limpian solo al completar el activo. Una respuesta incierta conserva el error y permite consultar la factura, sin reintento automático. No hay garantía nueva de idempotencia del POST documental frente a reintentos manuales tras una respuesta perdida; el contrato no la define. No se fusionan documentos por referencia.

### Estado de T008–T010

T008 parcial: creación de metadatos/lectura/líneas por altas nuevas están implementadas y probadas; el camino contractual de POST documental con items iniciales sobre activos existentes sigue 503. Faltan resolver su captura de fecha/motivo/revisión y orquestación con auditoría sin inventar parámetros funcionales.

T009: formulario e integración de compra para activos nuevos implementados y probados. Se conserva [ ] para el cierre integral del contrato de enlace de activos existentes, que no está habilitado por el servicio; no se presenta como interfaz de todo el alcance 003.

T010 parcial: todos los casos ejecutados del flujo factura-primero pasan; falta prueba positiva integral del camino de items iniciales mientras no exista implementación aprobada. No se marca completo un contrato aún bloqueado.

Evidencia vigente: backend completo 124/124, frontend completo 34/34 (20 anteriores + 14 nuevas), build PASS. Ninguna prueba ejecutada queda fallando. Esto no cierra T001–T007: mapeo/VALIDATE/NOT NULL, 005/008 reales, edición documental/custodio, reglas monetarias y las demás decisiones abiertas siguen pendientes. No se migró ni validó manualmente la instalación local.

## Cierre de asociaciones iniciales de compra — 2026-11-04

Esta sección actualiza el estado anterior: Alex confirmó explícitamente expected_revision, reason y fecha/motivo por item, solo activos existentes sin adquisición vigente y documento + todas las asociaciones en una transacción. No se crean activos ni se reemplazan líneas. No constituye aprobación de decisiones sobre donaciones, importes cero/negativos, cambio de origen ni edición compartida.

Cambios de esta continuación:
- backend/inventory/serializers.py: items estrictos, fecha exclusiva, revisión/motivo obligatorios y detección de ids repetidos (FR-008, FR-010, FR-011).
- backend/inventory/acquisition_services.py: orquestación atómica que reutiliza associate_asset, bloquea activos por id ascendente, conserva snapshots, revisión y moneda histórica (T006/T008).
- backend/inventory/views.py: POST documental utiliza el servicio real para compras con items; donaciones iniciales siguen indisponibles.
- backend/inventory/tests/test_acquisitions.py: seis casos API de asociación agrupada, entradas inválidas, revisión obsoleta, línea existente, referencia inexistente y rollback por fallo SQL real.
- backend/inventory/tests/test_acquisition_domain.py: tres casos independientes de integridad/rollback/concurrencia de asociación y uno de concurrencia API con items invertidos.
- backend/inventory/tests/test_operator_api.py: payload incompleto de compra ahora espera 400, conservando la comprobación de ausencia de escrituras.
- frontend/src/types.ts y api.ts: entrada tipada de asociaciones, sin enviar código visual al backend; errores anidados se normalizan por ruta.
- frontend/src/components/ExistingPurchaseItems.tsx (nuevo): consulta ficha real, conserva revisión consultada, prepara varios items, impide duplicados y permite retirarlos; no escribe hasta guardar factura.
- frontend/src/components/AcquisitionForm.tsx: integra asociaciones opcionales y errores por activo, preservando alta posterior de activos nuevos.
- frontend/src/tests/acquisition.test.tsx: tres pruebas nuevas de agrupación, conflicto sin reintento y ficha no elegible/errores anidados.
- contracts/api.md y contracts/web.md: registran la confirmación humana, sin extenderla a otros flujos.

Se preservaron todos los cambios anteriores. Rama verificada Alex_Sigcho_Feature. Sin migraciones nuevas ni aplicación a PostgreSQL local; sin cambios en .env, commits, push o PR. No se avanzó T011–T018.

Resultado final verificable: backend 134/134, frontend 37/37, compilación TypeScript/Vite correcta. T008, T009 y T010 se marcan completas en su alcance de compra aprobado. El paquete 003 permanece parcial; véanse pendientes en integration-notes.md.

## Donaciones T011–T013 — 2026-11-04

Alcance aprobado implementado (FR-007, FR-009, FR-010, FR-011, FR-012; SC-002/003): respaldo textual support_type + reference compartido, valores estimados individuales y alta posterior de activo+línea reutilizando el servicio existente. Alex confirmó para donaciones expected_revision, reason y fecha/motivo en items iniciales, solo activos existentes sin adquisición vigente y toda la operación en una transacción. La confirmación no se extiende a decisiones abiertas.

Archivos de esta continuación:
- backend/inventory/serializers.py: selección estricta de items por source; estimated_value de donación normalizado a item_value con Decimal(12,2). No se acepta item_value como alias en esos items.
- backend/inventory/acquisition_services.py: retirada del bloqueo provisional 503 de items de donación; reutiliza la misma orquestación, bloqueos por id, associate_asset, incremento global y AssetChange. No se duplicaron servicios ni endpoints.
- backend/inventory/tests/test_donations.py (nuevo): 15 pruebas de API/integridad/permisos/CSRF/rollback/concurrencia, en módulo separado para conservar las pruebas anteriores.
- frontend/src/components/AcquisitionForm.tsx: variante DONATION del mismo formulario; metadatos específicos y asociaciones existentes enviadas con estimated_value, alta posterior con item_value conforme a cada contrato.
- frontend/src/components/ExistingPurchaseItems.tsx: componente existente reutilizado con etiqueta de valor estimado y texto común de documento; conserva revisiones y protección frente a duplicados.
- frontend/src/components/Registration.tsx: etiqueta de valor estimado reutilizando campos base y fecha/motivo.
- frontend/src/App.tsx: acceso Registrar donación y panel conservado al ocultarse, con documento/estado separados de compra y desmontaje al salir de sesión.
- frontend/src/components/Inventory.tsx: ficha de donación presenta respaldo, tipo, valor estimado y fecha/motivo, sin total de factura.
- frontend/src/components/Form.tsx: nombres de errores para tipo de respaldo y valor estimado.
- frontend/src/api.ts y types.ts: entrada de donación tipada; transporte de sesión/CSRF, lectura y alta compartidos; mensajes de documento válidos para ambas fuentes.
- frontend/src/tests/donation.test.tsx (nuevo): nueve escenarios React con HTTP simulado únicamente en tests, usando cliente real.
- contracts/api.md, contracts/web.md: confirmación humana y límites actuales. tasks.md, validation.md, integration-notes.md y quickstart.md: evidencia y estado actualizado.

Atomicidad real: items iniciales confirman documento + todas las asociaciones/auditorías juntos. El flujo de activos nuevos confirma primero documento y después cada activo+línea por solicitud; un rechazo posterior conserva el respaldo y altas anteriores. No hay promesa de transacción entre solicitudes ni idempotencia ante respuesta perdida.

Estado: T011 parcial para el cierre integral de reglas de donación, aunque sus caminos aprobados están implementados. Continúan bloqueados por decisión humana la política de valores cero/negativos y la fecha documental; se conserva pending_decision sin inventar una política. T012 completa para el flujo aprobado; T013 completa para los requisitos definidos y pruebas de los límites explícitos, sin atribuir aceptación a políticas todavía no acordadas. T001–T007 mantienen sus pendientes y T014–T018 no se iniciaron.

No se crearon/modificaron migraciones, modelos ni gateways en este bloque. Se conservan cambios anteriores y la rama Alex_Sigcho_Feature. Sin migración/datos locales, .env, commits, push o PR. Trabajo asistido por IA; confirmación humana recibida únicamente para el payload de asociación de donaciones, revisión final de código pendiente.

## Edición y facultades T014–T017 — 2026-11-04

Contexto: rama verificada Alex_Sigcho_Feature; 44 rutas previas con cambios conservadas. Skill speckit-implement, feature explícita sin persistencia compartida, checklist requirements 10/10; sin hooks. Constitución continúa propuesta pendiente de ratificación. Este bloque no implementa T018.

T014: edición descriptiva y de línea reutiliza acquisition_services.update_asset, no se reescribe. PATCH de custodio sustituye 503 por custodian_services.update_custodian real. Alex confirmó reason + expected_profile y motivo en evidencia JSON, sin revisión de activos. El servicio conserva snapshots, autor/fecha, detecta perfil obsoleto bajo lock, traduce solo la restricción real de correo duplicado y revierte perfil/evidencia ante fallo SQL. No modifica custodia, entregas, devoluciones ni Movement.

T015: catálogo existente y selección inicial reutilizados. GET operador añade lectura activa/inactiva necesaria para corregir estado. change_asset_faculty prepara autorización, revisión global, guardia, lock, snapshots de facultades, incremento y AssetFacultyChange atómicos. La guardia de producción falla cerrada con 503 por proveedor 005 ausente. Éxito, pendiente, concurrencia y rollback se prueban con sustitutos únicamente en tests, sin declararlos integración real. Activos legados sin facultad no reciben una anterior ficticia.

T016: AssetEditForm, CustodianEditor y FacultyManagement integrados en App con diferencias antes/después, confirmación separada, motivo, errores y conservación de borradores. El cliente comparte CSRF/sesión y añade method PATCH. Operador sin Gestor solo consulta catálogo; no recibe permisos ordinarios. History muestra envoltura combinada y preserva contenido de movimientos/rectificaciones; la ruta 002 sigue disponible como alternativa explícitamente incompleta si falla la consulta combinada. Cambio posterior de facultad en UI permanece bloqueado por 005.

T017: módulo backend test_metadata_edit.py y frontend asset-edit.test.tsx. Incluye duplicados, reservados, revisiones/perfiles obsoletos, no escrituras en rechazo, autoría/snapshots, SQL real y carreras entre conexiones. Se mantiene pendiente la validación con proveedor real 005.

Archivos de código de esta continuación:
- backend/inventory/custodian_services.py (nuevo): servicio real de corrección auditada.
- backend/inventory/faculty_services.py: servicio de cambio y frontera ensure_no_pending_decommission.
- backend/inventory/serializers.py: FacultyChangeInput, CustodianProfileInput exacto y CustodianEditInput estricto.
- backend/inventory/views.py: conecta servicios reales y lectura de mantenimiento del catálogo.
- backend/inventory/tests/test_metadata_edit.py (nuevo): pruebas de edición, integración aislada y concurrencia.
- backend/inventory/tests/test_operator_api.py: entrada incompleta de custodio pasa a esperar 400, conservando ausencia de cambios.
- frontend/src/components/AssetEditForm.tsx, CustodianEditForm.tsx, FacultyManagement.tsx y ReviewChanges.tsx (nuevos): formularios y confirmación compartida.
- frontend/src/components/Form.tsx: valor inicial opcional en Field, sin modificar transporte ni validación existente.
- frontend/src/components/History.tsx: movimientos y snapshots de edición disponibles.
- frontend/src/App.tsx: integración de pantallas, permisos y consulta combinada independiente del detalle.
- frontend/src/api.ts y types.ts: PATCH con CSRF y tipo de envoltura histórica.
- frontend/src/tests/asset-edit.test.tsx (nuevo) y acquisition.test.tsx: aceptación nueva y adaptación de navegación Operador manteniendo prohibición de consultas ordinarias.
- SDD: contracts/api.md, contracts/web.md, data-model.md y los cuatro informes/estado solicitados.

No se modificaron modelos, migraciones, gateways ni funciones de paquetes ajenos en este bloque. No se aplicó migración local, no se tocaron .env/datos locales ni se hicieron commits/push/PR. Asistencia IA para implementación/pruebas; confirmación humana recibida para contrato de custodio. Revisión final por integrante pendiente.


</details>
