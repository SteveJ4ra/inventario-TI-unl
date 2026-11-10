# Integración 003 — estado final vigente

Rama Alex_Sigcho_Feature. Base prevista del PR: develop, nunca main. Referencia local origin/develop consultada: 4247cc8998ed810fdb6462941d85f3324260a2ec; no se hizo fetch, merge, commit ni publicación. No se afirma estar sincronizado con cambios remotos posteriores.

| Dependencia / contrato | Estado |
|---|---|
| Base 002 | Regresión completa aprobada; servicios/operaciones e historial conservados |
| 008, gateway de producción → import_assets | Integración real probada para compras nuevas y documentos existentes |
| 008, donación nueva por support_description | Bloqueada expresamente por Alex; 409 sin escrituras ni APPLIED ficticio |
| 005, solicitudes pendientes | Proveedor real ausente; cambio de facultad bloqueado con 503 |
| 006, licencias | Fuera de 003; no se declara proveedor integrado |
| PostgreSQL local | No migrado ni modificado |

## Contratos consolidados

PATCH documental aprobado: reason + snapshot completo expected_document + mapa expected_revisions de todos los activos actuales. Lock del documento antes de activos ordenados por id. Se compara pertenencia/revisiones y se audita documento y activos atómicamente. La respuesta de líneas añade asset_revision readonly; no hay columna nueva. Cambiar origen o moneda no está permitido por esta operación.

Custodio: reason + expected_profile completo, comparación bajo lock y evidencia JSON con perfil anterior/nuevo y motivo. No reescribe Movement ni aumenta revisiones de activos. El CAS por valores no detecta un ciclo A→B→A; no se afirma revisión monotónica de custodio.

CSV: import_assets(actor=..., rows=[values_normalizados...]) devuelve datos de registros realmente creados. Usa la misma validación y servicios 003, participa de la transacción 008 y deja la idempotencia a ImportBatch. document_key solo agrupa dentro del lote; no fusiona documentos por referencia. No se adaptó support_description por suposición.

## Acciones de otros integrantes / coordinación

1. 005 debe entregar una guardia real de solicitudes pendientes, coordinada con el mismo lock de Asset usado para crear/decidir solicitudes. Conectarla en ensure_no_pending_decommission; pendiente debe dar 409 y los errores reales deben propagarse. Después ejecutar los escenarios de cambio de facultad sin sustitutos y completar la UI bloqueada.
2. 008/coordinación deben acordar un tipo explícito de respaldo antes de habilitar donación nueva CSV. Las donaciones con documento existente ya funcionan.
3. Revisar conflictos de archivos compartidos y grafo al integrar develop; no se incorporaron ramas ajenas en este trabajo.

## T004 y decisiones humanas

- T004: Asset.faculty sigue nullable en el grafo activo. El dato de 0 activos locales fue aportado por Alex, no se consultó de nuevo ni se aplicaron migraciones a esa base. Para cualquier instalación se requiere inventario/mapeo de facultad verificado, resolución de textos incompatibles, revisión de todos los escritores (incluidos consumidores 002), VALIDATE de CHECK legados y promoción revisada de la contracción. No se inventan adquisiciones ni facultades.
- Decisiones humanas: importes cero/negativos y fecha documental de donación continúan con rechazo explícito pending_decision. Cambiar origen compra/donación no está habilitado. Alex indicó mantener bloqueada la donación nueva desde CSV; no se infiere support_type de support_description.
- 005: ensure_no_pending_decommission falla cerrada con 503 mientras falte el proveedor real. Cambio de facultad permitido/pendiente/concurrente está probado solo con sustitutos de esa guardia en tests, no con 005 real.
- 008: integración real verificada para compras nuevas por document_key y documentos existentes, incluida donación con documento existente. Creación de donación nueva por CSV no integrada por decisión expresa. El proveedor de licencias 006 queda fuera de 003.
- Revisión humana de entrega y despliegue pendientes. Constitución continúa propuesta; no se atribuye ratificación al equipo.


0004_acquisition_expansion depende de 0003_importbatch. La plantilla migration-notes/faculty_contract.py.txt no es una migración activa: aborta con facultades sin mapear, valida CHECK legados y prepara NOT NULL sin default. Fue probada únicamente en PostgreSQL temporal. Antes de promoverla, revisar escritores legados y el mapeo real; no asumir que el dato local de 0 activos prueba otras instalaciones.

## Recomendación de entrega

Preparar commits revisables tras revisión humana y abrir PR Draft hacia develop, con el cuerpo de pr-description.md. El alcance implementado puede revisarse ya; el paquete no está íntegramente cerrado y no se recomienda un PR normal listo para merge mientras los requisitos obligatorios abiertos no se resuelvan o difieran formalmente por el equipo.


<details>
<summary>Historial de bloques anteriores — sus estados no sustituyen el cierre vigente</summary>

# Integración y diseño técnico pendiente — 2026-11-04

Rama Alex_Sigcho_Feature; destino futuro develop. Base local registrada: 4247cc8998ed810fdb6462941d85f3324260a2ec. Sin commits ni cambios remotos. Grafo preparado: 0001_initial → 0002_integrity → 0003_importbatch → 0004_acquisition_expansion. 0004 se aplicó únicamente en PostgreSQL temporal; estado local no consultado ni modificado.

## Protección de datos: preparado frente a pendiente

Preparado en ORM: Asset/documento/línea no admiten delete normal ni QuerySet.delete; evidencia no admite update/bulk_update/delete y save fuerza INSERT para no sobrescribir un PK existente. PROTECT conserva referencias; Faculty referenciada no puede eliminarse por las relaciones declaradas. No se reemplaza la proyección mutable de Asset/documento/línea por evidencia inmutable. Movement conserva la protección PostgreSQL existente de 0002.

Diseño original antes de la expansión (actualizado por el apartado final): triggers BEFORE UPDATE OR DELETE de fila sobre las cuatro tablas nuevas de auditoría, rechazando con error explícito (patrón 0002, SQLSTATE 55000); triggers BEFORE DELETE sobre Asset/AcquisitionDocument/AcquisitionLine, incluso sin referencias. Considerar triggers BEFORE TRUNCATE de sentencia para esas tablas y evidencia, más revisión de privilegios de la cuenta de ejecución. No conceder permisos ni instalar triggers en este bloque. Los guards ORM no cubren _raw_delete, managers internos, SQL directo, TRUNCATE ni acciones de administradores de DB. Probarlos en PostgreSQL aislado al implementar T004; rollback no debe borrar evidencia o registros nuevos automáticamente.

En el bloque anterior los CHECK de textos se declararon sin esquema; ahora 0004 los instala, dejando NOT VALID los nueve de legado; su prueba evalúa sus predicados mediante SELECT sin crear tablas. T004 requiere preflight del legado y abortar ante textos inválidos, sin recortar ni inventar valores históricos automáticamente.

## Revisión global

Declarados CHECK resulting_revision > 0 y UNIQUE(asset, resulting_revision) por tabla de auditoría de activo/facultad. No garantizan exclusión entre tablas ni igualdad con Asset.revision. Una FK/CHECK local no puede expresar por sí sola ese vínculo entre filas/tablas. T006 debe bloquear Asset con select_for_update, comprobar expected_revision, incrementar exactamente una vez y crear evidencia con esa revisión en la misma transacción. Documento compartido bloquea activos por id y registra un evento documental más evidencia por activo. No modificar revisiones de eventos antiguos cuando avance la proyección. Probar carreras y rechazo de rectificación antigua al implementar T006/T017.

## Cinco asuntos funcionales pendientes de aprobación

| Asunto | Estado y parte que se mantiene pendiente |
|---|---|
| Importes cero/negativos | No fijado por Alex para 003. 008 ya rechaza negativos en _money; la admisión efectiva de cero debe revisarse por campo. No agregar CHECK de signo hasta acordar política común. Decimal(12,2) es precisión técnica, no aprobación del signo. |
| support_description → support_type | El CSV 008 usa descripción libre; 003 usa tipo + referencia confirmado. No asumir equivalencia ni convertir históricos automáticamente. import_assets sigue pendiente. |
| Fecha documental de donación | No se confirmó obligatoriedad ni prohibición. El campo es nullable por compras/donaciones; que el modelo actualmente permita fecha en donación no es aprobación de su API. |
| Cambio PURCHASE/DONATION con líneas | No se confirmó si es admisible ni qué validación/auditoría requeriría. No implementar esa edición. |
| Concurrencia de documento compartido | Ya confirmado: expected_revision de todos los activos, bloqueos por id, incremento y auditoría atómicos. Pendientes: forma del payload, documento sin activos, carrera con asociación de nuevas líneas y edición simultánea de metadatos. Propuesta técnica para revisar: bloquear primero el documento y después activos por id; las asociaciones de líneas deben respetar el mismo orden. No se afirma que esté implementado/aprobado todo el protocolo. |

## Dependencias

002 presente: 45 pruebas existentes conservadas, dentro de la selección verde final de 65. Al activar nuevas altas/PATCH se actualizarán sus expectativas de contrato donde 003 lo extiende, sin quitar protección DELETE ni relajar invariantes.

005 no integrado: no crear DecommissionRequest propio ni éxito ficticio. El futuro cambio de facultad debe integrar la comprobación de solicitud pendiente; no existe aquí una ruta que eluda ese bloqueo.

008 presente: guarda explícita de tablas ausentes antes de consultar referencias; no valida columnas ni constraints ni disponibilidad del servicio. Conexión rota, consulta incompatible y dependencia interna rota se propagan como errores reales. La introspección completa simulada en tests no demuestra integración real. Espera inventory.acquisition_services.import_assets(actor=..., rows=[values]); todavía no existe. No se modifica su parser, plantillas, ciclo de confirmación ni reglas funcionales. 006 sigue ausente para lotes de licencia. Las pruebas existentes de importación usan FakeGateway, sin convertirlo en proveedor real.

## T004: propuesta original; expansión realizada y completado aún pendiente

Después de cerrar decisiones y revisar diseño: expansión con tablas/FK Asset.faculty nullable; mapeo verificado por identificador estable, completado controlado transaccional; rechazo de cobertura incompleta o contradictoria; nueva comprobación antes de NOT NULL. Base local con 0 activos según Alex, no consultada en este bloque; recomprobar al aplicar. No crear adquisición/facultades ficticias. Conservar adquisición histórica ausente hasta obtener datos verificados. Coordinar NOT NULL con T005–T007 para no romper el alta 002; detener escrituras durante el paso sensible. Revisión humana obligatoria antes de generar/aplicar conforme a la restricción actual de Alex.


## Estado vigente tras expansión autorizada

La propuesta de triggers UPDATE/DELETE anterior ya está implementada en 0004. Los párrafos que describían SQL pendiente corresponden al estado previo; las protecciones vigentes son las verificadas en validation.md. La nueva migración no se revierte automáticamente: su último RunSQL tiene reverse_sql=None y Django rechaza el retroceso antes de ejecutar operaciones destructivas. No usar --fake para evitar esa protección; cualquier reversión futura necesita un plan humano que conserve datos.

Los nueve CHECK de textos sobre tablas preexistentes permanecen NOT VALID. No se ejecutó VALIDATE CONSTRAINT ni se modificaron valores anteriores. Un UPDATE de una fila histórica inválida también será rechazado hasta su corrección autorizada; esto puede bloquear su futuro mapeo de facultad, por lo que el preflight debe identificarla. Los CHECK de las tablas nuevas sí están instalados/validados. Las FK, OneToOne y UNIQUE de nuevas auditorías se probaron en PostgreSQL; la revisión global entre tablas sigue a cargo de T006.

Alcance de conservación probado: UPDATE/DELETE de cuatro auditorías, DELETE de activos/documentos/líneas y protección por FK de facultades referenciadas. TRUNCATE, DROP y desactivación de triggers por el propietario/administrador no se bloquean con estos triggers de fila; revisar privilegios de despliegue antes de habilitar un servicio real. No se cambiaron roles locales ni se relajó la prueba de concurrencia/limpieza de PostgreSQL temporal. No afirmar protección total contra operaciones privilegiadas.

Compatibilidad: la facultad nullable permite el alta 002 sin nuevos campos. ImportBatch, su contenido histórico y su suite existente se conservan. 008 ya puede encontrar las tablas en el entorno temporal, pero acquisition_services.import_assets sigue ausente y no se simuló un alta real. Su adaptación support_description/support_type continúa pendiente. Los cinco asuntos funcionales de la matriz anterior siguen pendientes de aprobación.

Para cerrar T004: preparar mapeo explícito verificado y procedimiento de completado atómico que aborte ante faltantes/contradicciones; revisar textos incompatibles sin corregirlos automáticamente; VALIDATE de CHECK legados; después de adaptar T005–T007, nuevo preflight y NOT NULL de faculty. Aunque la base local tenga cero activos, hay que recomprobarlo al aplicar. Riesgos de aplicación: bloqueos de DDL, rechazo de nuevas escrituras de textos inválidos y falta de rollback automático; revisión previa de Alex y copia de seguridad antes de despliegue.


## Estado vigente T005/T006 — 2026-11-04

0004 se revisó y sus diez pruebas se repitieron antes del desarrollo. Ningún cambio estructural ni de migración en este bloque. Los CHECK NOT VALID siguen conservando legado previo y validando nuevas escrituras, los triggers siguen funcionando sin impedir las operaciones legítimas probadas de 002/008. Límites de TRUNCATE/privilegios y futura obligatoriedad de faculty permanecen.

Primitivas reales disponibles en inventory.acquisition_services: create_document(actor=..., data=...), create_asset_with_acquisition(actor=..., data=...), associate_asset(actor=..., document_id=..., asset_id=..., data=...) y update_asset(actor=..., asset_id=..., data=...). create_asset de services deriva a la variante de adquisición cuando recibe campos 003; sin ellos conserva el flujo 002 hasta activar T007. El API de 002 no acepta todavía esos campos: se mantiene su serializador anterior. No habilitar el flujo como 003 completo antes de T007.

Orden técnico aplicado dentro de cada transacción: documento primero, facultad en alta y luego activo/línea cuando existan. update_asset lee el id documental, bloquea documento y activo y vuelve a comprobar el vínculo antes de editar; una asociación concurrente diferente causa conflicto. No hay servicio de reasignación ni de edición documental. Las carreras probadas son alta duplicada con documento compartido y dos ediciones del mismo activo con igual expected_revision, con un ganador y un conflicto. No se declara validado el protocolo pendiente de editar un documento y asociar simultáneamente activos.

La revisión global se incrementa una vez por edición/asociación, junto a AssetChange en una misma transacción. Snapshots incluyen valores decimales serializados, fecha/motivo y currency persistida en documento, no la configuración actual. Movimientos y sus snapshots no se reescriben. La guarda de record_operation y el helper assets de la vista rechazan/ocultan la rectificación de movimientos cuya resulting_revision ya no coincide. No hay nuevos endpoints.

Frontera 008: acquisition_services ahora existe, pero import_assets(actor, rows) sigue sin publicarse. Un futuro adaptador debe normalizar las filas de 008, agrupar por document_key explícita (sin fusionar por reference), validar metadatos del grupo y ejecutar estas mismas primitivas bajo una transacción de lote; revalidar FK/identidad al aplicar. No duplicar reglas ni convertir support_description en support_type por suposición. La ausencia de la función sigue comunicándose como ProviderUnavailable, sin éxito ficticio. Los tests de importación existentes continúan verdes con su FakeGateway; no son integración con este proveedor real.

Decisiones pendientes sin escrituras: cero/negativos y fecha documental explícita de donación devuelven pending_decision en los servicios; no se añaden constraints ni se determina que sean funcionalmente inválidos. El tratamiento definitivo, el cambio de origen con líneas y la concurrencia de edición documental requieren aprobación. Creación inicial de documento con items no vacíos queda para el orquestador posterior, no se ignora silenciosamente.

Para continuar T005/T006: cerrar decisiones funcionales, completar edición/auditoría de documentos compartidos con expected_revision de todos los afectados, probar asociación/edición documental concurrente y el adaptador de 008 real cuando su mapeo esté acordado. T007–T018 siguen fuera de este encargo. T004 sigue parcial y no aplicada localmente.


## T007 — integración de sesión/rutas autorizadas, estado vigente

create_operator usa el patrón seguro de create_gestor, solo grupo Operadores. Sesión login/me/logout admite Gestores/Operadores activos; permissions técnicos inventory.manage/faculties.manage no conceden roles por sí mismos. Permiso global IsManager no se cambia: 005/006/008 no se amplían al Operador. IsManagerOrOperator solo se aplica a sesión/lista activa de facultades; catálogo de escritura usa IsOperator. CSRF se conserva. No se crearon revisores ni flujos exclusivos de otros paquetes.

Alta API 003 activada: POST /assets exige faculty_id, acquisition_document_id, item_value y fecha/motivo junto a 002. Los servicios internos mantienen la compatibilidad transitoria de creación de legado, pero la API no acepta nuevas fichas incompletas. Las pruebas API antiguas se adaptan con datos válidos de 003 sin perder sus aserciones. La interfaz Registration aún no se adapta: queda para sus tareas autorizadas posteriores; no declarar listo su recorrido manual. AssetOutput añade faculty_id/adquisición sin retirar campos anteriores.

Rutas conectadas a servicios reales: metadatos/lectura de adquisición, catálogo, PATCH de activo y GET history. history mezcla Movement/AssetChange/AssetFacultyChange por revisión descendente y mantiene /movements sin reemplazarlo. Cambio de facultad queda 503 mientras no exista la regla 005 real; no se usa un fake de ausencia de solicitudes. PATCH de documento es 409 pending_decision; PATCH custodio es 503 por servicio no implementado. Orquestación de items iniciales no vacíos también 503. No se cambian documentos/perfiles/facultades en esas ramas.

No existe nueva migración: grafo sigue 0001→0002→0003→0004, probado temporalmente. No se aplicó nada local. T004 aún necesita mapeo/saneamiento autorizado de legado, VALIDATE de CHECK y NOT NULL posterior. No tocar 005/006/008 para lograr un resultado verde; import_assets continúa pendiente de mapeo y las pruebas de importación con FakeGateway conservan su alcance aislado.

Resultado actual: 118/118 backend completos y 20/20 frontend/build PASS. Doce métodos de aceptación anteriores pasaron de rojo a verde; el decimotercero ya aprobaba denegación por rol y ahora cubre endpoint existente. No confundir suite actual verde con implementación de las ramas bloqueadas o aceptación de decisiones pendientes. Revisar tabla de T001–T007 en implementation.md antes de marcar una tarea.


## Compras web T008–T010 — 2026-11-04

App activa el alta por compra mediante AcquisitionForm, con documento previo y una transacción independiente por activo/línea. Reutiliza endpoints y servicios T005–T007; get_document centraliza la lectura autorizada y prefetch de códigos. No hay nuevo endpoint, tabla, migración, agregado de lote ni duplicación de reglas de alta. GET de líneas añade asset_code readonly. Se conservan las operaciones y el historial anteriores.

La UI admite factura nueva o seleccionada por id explícito, mantiene el documento durante varios registros y consulta su estado real. No crea una factura por cada activo ni compara referencia para fusionar documentos. Mantiene valores como cadenas y envía facultad/id de documento numéricos; toma currency de la respuesta para importes históricos y nunca la manda como selección. Errores del servidor se muestran en resumen y junto a campos; rechazos/información incompleta no se convierten en éxito. No se asignan facultades, fechas, valores ni datos históricos por defecto.

Se preserva el componente y su bloqueo al ocultar/reabrir el panel, evitando perder un POST en curso y permitir otro inadvertido. El estado vive solo en Workspace y se descarta al cambiar usuario/logout. La guardia frontend usa inventory.manage; Operador sin ese scope no solicita inventario/compras, y la autorización real continúa en backend. No se ofrece administración de facultades/revisores ni UI de donación en este bloque.

Atomicidad probada: un POST /assets fallido no deja activo ni línea. El documento fue creado antes y se conserva conforme al flujo; registros anteriores exitosos no se revierten al fallar uno posterior. El cliente informa solo líneas/códigos confirmados. La falta de idempotencia documental para un reintento manual tras pérdida de respuesta sigue siendo límite del contrato, sin deduplicar por reference ni prometer exactly-once. No se añaden restricciones de signo/moneda ni decisiones funcionales.

T008 y el cierre integral T009/T010 permanecen parciales por POST /acquisitions con items existentes, aún bloqueado. Su contrato compacto no define cómo aportar fecha/motivo/revisión/motivo de cambio de cada activo; el servicio associate_asset ya exige esas garantías, por lo que no se omiten ni se inventan. La UI de compras nuevas funciona sin depender de esa rama.

Regresión vigente: 124 backend en PostgreSQL temporal; 34 frontend con HTTP simulado y build PASS. Sin navegador real contra el servidor local ni migración local. Los tests de 008 siguen con su FakeGateway; import_assets real/adaptación support_description, 005 real, edición de documento/custodio y las decisiones previas permanecen pendientes. Esquema local, mapeo histórico, VALIDATE de CHECK y NOT NULL no se modificaron.

## Actualización de compra con items — 2026-11-04

La definición de items de compra fue confirmada por Alex: activos existentes sin adquisición, revisión esperada, motivo y fecha/motivo por línea. El POST documental ahora reutiliza associate_asset en una transacción exterior, bloqueando activos en orden id. Ante cualquier error no persisten documento, líneas, incremento de revisión ni auditorías parciales. No se inventa ni cambia facultad de un activo histórico. El alta nueva sigue siendo POST documento seguido de POST /assets atómico por activo; no es una transacción global entre solicitudes HTTP.

008 sigue pendiente de inventory.acquisition_services.import_assets y de adaptación support_description/support_type. No se modificaron proveedores ni se simula éxito. 005 sigue pendiente para cambios de facultad. T004 conserva mapeo histórico autorizado, validación de constraints históricos y obligatoriedad final de facultad pendientes. Continúan pendientes edición documental compartida, edición de custodio, donaciones iniciales y políticas no confirmadas (cero/negativos, fecha documental de donación, cambio de origen, concurrencia de edición compartida). No inferir cierre de T001–T007 por suites verdes.

## Estado actual de donaciones y decisiones abiertas — 2026-11-04

Base local de referencia origin/develop: 4247cc8998ed810fdb6462941d85f3324260a2ec (git rev-parse, sin fetch ni integración de ramas). Rama Alex_Sigcho_Feature. Grafo sin cambios: 0004_acquisition_expansion depende de 0003_importbatch y solo se ha aplicado en clúster temporal. 002 y gateway CSV se conservan y pasan la regresión; import_assets sigue ausente, no se devuelve éxito ficticio.

Confirmado por Alex: items de donación usan estimated_value, expected_revision, reason y fecha/motivo; solo activos sin adquisición vigente y documento + asociaciones atómicos. La API normaliza únicamente estimated_value a AcquisitionLine.item_value; esto no implica mapear support_description a support_type.

| Decisión humana pendiente | Opciones que requieren acuerdo | Comportamiento actual |
|---|---|---|
| support_description de 008 frente a support_type de 003 | Añadir tipo explícito a CSV/contrato 008; o aprobar un adaptador con semántica y mapeo verificables. No deducir tipo de una descripción libre. | Integración import_assets pendiente; 003 acepta support_type explícito. |
| Valores cero/negativos | Acordar >0; admitir cero y rechazar negativos; o definir casos concretos para valores firmados con su semántica. El modelo no resuelve la decisión. | <=0 devuelve 409 pending_decision antes de escribir; positivos usan precisión aprobada. |
| Fecha documental de donación | Acordar campo opcional o campo obligatorio; si obligatorio, definir tratamiento de documentos existentes sin inventar fechas. | Flujo aprobado omite el campo; presencia explícita devuelve 409 pending_decision. Fecha/motivo por activo sí obligatorios. |
| Cambio compra/donación con líneas | Prohibición estable o conversión auditada con precondiciones y revisiones de todos los afectados, por definir. | PATCH documental no habilitado; no se reemplazan líneas. |
| Edición concurrente de documento compartido | Concretar colección de revisiones, documento vacío y carreras de asociación durante la edición. | Asociación inicial usa locks y revisiones; no supone completado el protocolo PATCH. |

T004 conserva mapeo histórico verificado, saneamiento/VALIDATE y facultad obligatoria pendientes. 005 conserva cambio de facultad pendiente; 008 conserva proveedor real/adaptación pendiente. La edición de custodios y documental permanece pendiente. No se implementaron funcionalidades de 005/006/008 ni T014–T018.

La nueva asociación de un activo histórico no inventa facultad: conserva la que ya tenga, incluida nulabilidad temporal. La auditoría registra antes/después, moneda persistida y revisión, sin reescribir Movement ni habilitar rectificación antigua.

## Estado vigente T014–T017 — 2026-11-04

Esta sección sustituye el bloqueo histórico de PATCH custodio: ya existe custodian_services.update_custodian real, confirmado por Alex con expected_profile/reason. Los snapshots de Movement no se reescriben, Asset.revision no aumenta por corrección del perfil y CustodianChange conserva evidencia protegida por la migración existente. La comparación por valores detecta un perfil distinto al consultado, no un ciclo A→B→A; una revisión monotónica propia requiere decisión/modelo/migración posteriores, no se declara implementada.

005 sigue ausente. Punto de integración preparado: faculty_services.ensure_no_pending_decommission(asset=asset), invocado bajo select_for_update del activo y dentro de la transacción de cambio. Hoy lanza DependencyUnavailable (503), nunca False ni éxito. Al recibir proveedor real, conectar su comprobación bajo el mismo lock y coordinar ese lock con creación/decisión de solicitudes de 005; pendiente implica 409 y errores de DB/proveedor deben propagarse. No se inventa nombre de módulo/modelo ajeno ni se captura un error real como ausencia de solicitudes.

El resto de change_asset_faculty está preparado: permiso Operador, revisión, referencia destino, motivo, snapshots, AssetFacultyChange e incremento global; probado aisladamente con guardias sustituidas solo en tests. Con datos legados sin facultad previa se conserva bloqueo de T004; no se genera evento con una facultad anterior inventada. UI no ofrece confirmar ese cambio mientras falte la protección real. T015/T016/T017 conservan validación/funcionalidad parcial por esa dependencia.

La lectura GET /operator/faculties/ incluye inactivas para poder reactivarlas, con el mismo permiso Operador de mantenimiento; GET /faculties/ sigue activo-only y el alta sigue asignando la selección explícita del Gestor. El perfil Operador no consulta /assets, /options ni /custodians por iniciar sesión.

Persisten T001–T007 parciales sin cierre automático por suites verdes, T004 (mapeo verificado/VALIDATE/obligatoriedad), T011 (políticas monetarias/fecha documental), import_assets 003/008 y adaptación support_description/support_type, edición concurrente documental y cambio de origen. T018 sin iniciar; no se tocaron README ni se publicó PR. Las nuevas consultas combinadas usan el contrato transversal sin reemplazar /movements/.

Base de integración consultada sin fetch: origin/develop 4247cc8998ed810fdb6462941d85f3324260a2ec. Rama Alex_Sigcho_Feature. Grafo intacto: 0004_acquisition_expansion → 0003_importbatch. No se modificó/aplicó migración local. Regresión con proveedor real 005/008: NO INTEGRADA; pruebas con guardias sustituidas no son evidencia de esa integración.


</details>
