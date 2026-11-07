# Contratos API: fichas y adquisición

Todos los endpoints requieren sesión autenticada según rol. Las mutaciones usan CSRF. Campos desconocidos o reservados se rechazan.

| Método y ruta | Actor | Resultado |
|---|---|---|
| GET /api/faculties/ | Gestor / operador | Lista activa de facultades |
| POST /api/operator/faculties/ | Operador | Añade facultad |
| PATCH /api/operator/faculties/{id}/ | Operador | Corrige nombre/estado sin borrar referencias |
| POST /api/acquisitions/ | Gestor | Crea documento PURCHASE o DONATION y sus líneas |
| GET /api/acquisitions/{id}/ | Gestor | Documento común y activos/importes enlazados |
| PATCH /api/acquisitions/{id}/ | Gestor | Corrige datos con motivo y auditoría |
| PATCH /api/assets/{id}/ | Gestor | Edita solo campos descriptivos y adquisición con reason obligatorio; facultad se rechaza como campo reservado |
| PATCH /api/operator/assets/{id}/faculty/ | Operador | Cambia facultad con motivo e historial; 409 si hay solicitud de baja pendiente (regla completada en 005) |
| PATCH /api/custodians/{id}/ | Gestor | Edita nombre/correo/dependencia, preservando snapshots |
| GET /api/assets/{id}/history/ | Gestor | Orden cronológico combinado de movimientos y cambios de ficha |

Purchase request: reference, document_date, supplier, invoice_total, items[{asset_id, item_value, expected_revision, reason, acquired_on|date_unknown_reason}].
Donation request: reference, support_type, items[{asset_id, estimated_value, expected_revision, reason, acquired_on|date_unknown_reason}].
Asset date: acquired_on o date_unknown_reason; exactamente una alternativa válida.
Asset edit: reason y solo campos descriptivos/adquisición; facultad y cambios de estado se rechazan en esta ruta. Faculty change usa ruta de operador, reason y before/after audit.
Currency: respuesta monetaria incluye currency=USD; cliente no puede elegir otra moneda.

Errores: 400 validación, 403 acceso, 404 inexistente, 409 duplicado/conflicto; sin cambios parciales ante error.

## Extensión de alta y acceso

POST `/api/acquisitions/` admite metadatos del documento con `items` omitido/vacío; items, si se aportan, solo enlaza activos existentes. POST `/api/assets/` mantiene los campos de 002 y exige `faculty_id`, `acquisition_document_id`, `item_value` y exactamente una alternativa `acquired_on`/`date_unknown_reason`. El documento y la facultad deben existir; tipo del documento determina valor de compra o estimado. Activo y línea se guardan juntos o nada.

PATCH de activo/facultad y documento compartido exige `expected_revision` (documentos: revisiones de todos los activos afectados). La facultad inicial la indica el Gestor al registrar; cualquier cambio posterior solo se hace por la ruta de Operador. Se implementan provisión y sesión de Operador en este incremento, según contratos transversales.

## Aclaración confirmada — 2026-11-04

Donación: support_type + reference. La fecha o motivo pertenece a AcquisitionLine. Corregir documento produce AcquisitionDocumentChange y un AssetChange por cada activo afectado en una misma transacción; cada activo incrementa su revisión. El formato exacto de la colección de expected_revision por activo sigue pendiente de concretar antes de implementar PATCH documental.

008 publica actualmente support_description; el adaptador debe acordarse explícitamente antes de conectar import_assets. No tratar una descripción libre como un tipo de respaldo por suposición.


## Límites de aprobación pendientes — 2026-11-04

No están resueltas la política cero/negativos, la traducción support_description de CSV a support_type, la fecha documental de donación ni la conversión compra/donación con líneas. Para concurrencia se conserva lo ya requerido (revisiones de activos, bloqueos y auditoría atómicos); payload de revisiones, documento sin activos y carrera de asociación de líneas siguen por concretar. No se expone un PATCH permisivo por deducirlo del modelo provisional.


## Estado técnico de exposición T007 — 2026-11-04

Las rutas aprobadas se conectan a servicios reales de metadatos de documento, alta completa, edición de activo, catálogo e historia. POST /assets ya exige los campos de 003. La salida añade faculty_id y acquisition (snapshot con currency persistida); GET/POST documento devuelve items con asset_id, item_value, acquired_on y date_unknown_reason. item_value es compra o estimación según source; desde T011 la entrada estimated_value de items de donación se normaliza a ese campo de línea, sin aceptar item_value como alias en esos items.

Permisos de sesión técnicos: inventory.manage para grupo Gestores y faculties.manage para Operadores; no hay concesión de Gestor por login Operador. must_change_password=false en 003. Respuestas de sesión/CSRF conservan el flujo transversal.

Indisponibilidad explícita, sin éxito simulado: PATCH de facultad del activo devuelve 503 dependency_unavailable mientras falte la integración 005; PATCH de custodio ya usa el servicio auditado real definido en la confirmación T014; alta documental de donación con items no vacíos ya utiliza la orquestación transaccional confirmada en T011. PATCH documental devuelve 409 pending_decision. Estos estados documentan implementación parcial, no sustituyen la aceptación futura definida arriba ni resuelven las decisiones funcionales pendientes. No se habilitan operaciones incompletas.

## Confirmación humana: asociaciones iniciales de compra (2026-11-04)

Alex confirmó expresamente ampliar cada item de compra con expected_revision, reason y exactamente una alternativa acquired_on/date_unknown_reason. Solo se asocian activos existentes sin adquisición vigente. Documento, todas las líneas, revisiones y auditorías se guardan en una transacción. No se crean activos ni se sustituyen líneas. Omitir items o enviarlo vacío sigue creando solo el documento; POST /assets conserva el alta posterior atómica de activo + línea.

Items repetidos, campos reservados, fechas incompletas y payload inválido: 400 sin escrituras. Activo inexistente: 404. Revisión obsoleta: 409 stale_revision; adquisición vigente: 409 acquisition_exists. Cualquier fallo revierte también el documento nuevo. Sin orden contractual de respuesta. Esta confirmación es exclusiva de compras: no resuelve items de donación, fecha documental de donación, política de cero/negativos, cambio de origen ni edición concurrente del documento compartido.

## Confirmación humana y estado de donaciones T011–T013 — 2026-11-04

Alex confirmó expresamente expected_revision, reason y exactamente una alternativa acquired_on/date_unknown_reason por item de donación. Solo admite activos existentes sin adquisición vigente; documento, líneas, incremento de revisiones y AssetChange se confirman o revierten juntos. Se reutiliza la misma orquestación de compra y el mismo associate_asset, con locks de activos por id ascendente. No se crean activos a partir de items ni se reemplazan líneas.

Entrada inicial de donación: source=DONATION, reference, support_type, items opcionales con asset_id, estimated_value, expected_revision, reason y fecha/motivo. estimated_value se almacena en AcquisitionLine.item_value; las respuestas mantienen item_value, tal como en el contrato de salida existente. POST /assets conserva item_value para el valor estimado de un activo nuevo: no cambia su contrato a estimated_value. Ambos flujos usan USD persistido.

Documento sin items no modifica activos. El alta posterior de cada activo y su línea es atómica, pero no existe una transacción entre dos solicitudes HTTP distintas. Un fallo posterior conserva el documento previamente confirmado y los activos anteriores.

Proveedor/total de factura, currency, support_description, autor, snapshots y otros campos reservados no se aceptan. Repetidos/fechas inválidas/campos incompletos: 400; referencia de activo inexistente: 404; revisión obsoleta: 409 stale_revision; adquisición vigente: 409 acquisition_exists. Sin escrituras parciales. Permisos Gestor y CSRF siguen siendo obligatorios (403).

Límites anteriores conservados: importes <=0 y fecha documental explícita de donación devuelven 409 pending_decision. La omisión de document_date permite el flujo aprobado de respaldo textual y no representa decisión sobre obligatoriedad futura. PATCH documental/cambio de origen continúa sin habilitarse. Esta confirmación no aprueba adaptación con CSV ni políticas pendientes.

## Edición T014–T017 y confirmación humana de custodios — 2026-11-04

Alex confirmó exigir reason y expected_profile para PATCH /custodians/{id}/. expected_profile contiene exactamente full_name, email y department del perfil consultado (sin id/revisión); los campos a corregir son opcionales y se limitan a esos tres. El servicio valida, bloquea Custodian, compara el snapshot completo y devuelve 409 stale_profile si difiere. Crea CustodianChange con before_json={profile: perfil_anterior}, after_json={profile: perfil_nuevo, reason: motivo}, actor y fecha del servidor. No incrementa Asset.revision ni reescribe Movement, custodian_snapshot o custodia vigente. No se añade un contador al custodio ni se cambia el esquema. Error de correo duplicado: 409 duplicate_custodian; entradas inválidas/reservadas: 400; inexistente: 404; roles/CSRF: 403. Perfil y evidencia se guardan o revierten juntos.

GET /operator/faculties/ completa la lectura de mantenimiento para el Operador e incluye facultades activas e inactivas; GET /faculties/ conserva la lista activa para altas. POST/PATCH del catálogo conservan sus contratos y permisos, sin borrado ni nueva auditoría funcional inventada.

PATCH /operator/assets/{id}/faculty/ recibe faculty_id, reason y expected_revision. El servicio bloquea activo, comprueba revisión y ejecuta ensure_no_pending_decommission(asset=asset) dentro de la transacción. La guardia actual devuelve 503 dependency_unavailable porque 005 no publica proveedor real: no asume ausencia de solicitudes ni confirma cambios. Cuando se conecte el proveedor debe lanzar conflicto si hay solicitud pendiente y propagar fallos reales; conservar lock del mismo activo y coordinarlo con creación/decisión de solicitudes en 005. Solo tras superar esa guardia se bloquea la facultad destino, guarda proyección, incrementa revisión y crea AssetFacultyChange con ids/nombres anterior y nuevo. Un activo legado sin facultad previa queda bloqueado por mapeo T004 pendiente; no se inventa su origen.

PATCH de activo mantiene AssetEditInput, expected_revision global, reason, bloqueo, auditoría y restricciones de campos reservados. No incorpora edición del documento compartido ni conversión de origen. GET /assets/{id}/history/ conserva movimientos y eventos asset_change/faculty_change disponibles. La auditoría del perfil de custodio es independiente y no se atribuye artificialmente a activos.

## Contrato vigente de cierre documental e importación — 2026-11-04

Alex confirmó PATCH /acquisitions/{id}/ con reason, expected_document (todos los campos source, reference, document_date, supplier, invoice_total, support_type, currency del documento consultado) y expected_revisions como mapa de cadenas id → revisión de todos sus activos actuales. Campos editables: compra reference/document_date/supplier/invoice_total; donación reference/support_type. source y currency reservados; fecha documental de donación explícita e importes <=0 siguen 409 pending_decision. No hay conversión de origen.

Se bloquean documento y activos por id, se comparan snapshot, conjunto de ids y revisiones, y se guardan evento documental más un AssetChange/incremento por activo en una transacción. Snapshot o pertenencia obsoletos: 409 stale_document; revisión de activo obsoleta: 409 stale_revision. Documento vacío exige expected_revisions={} y snapshot, y conserva su evento. No hay cambio parcial ante error. Items de respuesta añaden asset_revision readonly.

Proveedor 008 real: inventory.acquisition_services.import_assets(actor=..., rows=[values_normalizados...]) devuelve {created, asset_ids, document_ids} tras crear realmente los registros. Compras nuevas agrupadas por document_key y adquisiciones con documento existente reutilizan servicios 003. Todo el lote se revierte ante fallo y la idempotencia pertenece a ImportBatch de 008. No se permite editar metadatos de documento existente por CSV ni enviar campos reservados.

Decisión expresa de Alex: mantener bloqueada la donación nueva por CSV hasta contrato de tipo explícito; no se convierte support_description a support_type. Devuelve 409 pending_decision, sin escrituras ni APPLIED ficticio. Donaciones con acquisition_document_id existente no requieren ese adaptador y están probadas con gateway de producción. Las secciones previas que describen indisponibilidad general de import_assets/PATCH documental son evidencia histórica sustituida por este estado.
