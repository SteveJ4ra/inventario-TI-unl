# Contratos técnicos compartidos de 003–008

Estas decisiones de implementación concretan las reglas confirmadas sin agregar funcionalidades. Cada plan y contrato de feature debe respetarlas. 002 conserva su especificación histórica; las extensiones siguientes se implementan en las features indicadas.

## Sesión y permisos: base en 003, ampliación en 005

003 introduce el permiso Operador, su comando local de provisión y acceso a login/me/logout, administración de facultades y cambio auditado de facultad. 005 reutiliza ese permiso y añade Revisor; no vuelve a crear el operador. Los endpoints ordinarios de inventario permanecen exclusivos de Gestores. No se concede acceso de Gestor por ser Operador o Revisor.

`GET /api/auth/me/` y login devuelven `{id, username, permissions: [string], must_change_password: boolean}`. En 003 no hay revisor ni cambio inicial obligatorio; en 005 la cuenta revisora temporal solo puede consultar su sesión, cerrar sesión y cambiar contraseña hasta completarlo. El cliente obtiene nuevamente CSRF tras login. Sesión ausente, usuario inactivo o permiso insuficiente: HTTP 403, como 002; no se introduce 401 con la autenticación de sesión actual. El inicio rechazado no deja una sesión autorizada.

## Revisión, historial y rectificación

Toda mutación de un activo usa bloqueo del activo, `expected_revision`, validación del estado vigente y una única transacción. Incluye cambios descriptivos/adquisición/facultad de 003, eventos de 004 y bajas/solicitudes/decisiones de 005. Cada evento que afecte la ficha o su elegibilidad incrementa `Asset.revision` y registra `resulting_revision`; el cliente nunca asigna la revisión resultante. Una edición de documento compartido bloquea los activos afectados en orden de id, audita e incrementa sus revisiones.

La rectificación existente solo es elegible si `target.resulting_revision == asset.revision`, además de las restricciones de 002. Por tanto, un movimiento anterior no vuelve a ser elegible después de una edición, novedad, mantenimiento, solicitud o rectificación. Consultas/descargas no cambian revisión. Cambiar el perfil de un custodio conserva snapshots y no reescribe movimientos.

`GET /api/assets/{id}/movements/` conserva su contrato histórico. La nueva ruta `/history/` mezcla movimientos y eventos/auditorías de features mediante una envoltura `{event_type, event_id, occurred_at, actor, resulting_revision, data}`; se ordena por revisión descendente cuando exista y por fecha/tipo/id para desempate. No se sustituyen ni borran filas antiguas.

## Localización y custodia en 004/005

Se mantiene la condición de 002 y sus valores de API `operativo`, `averiado`, `en_reparacion`. En activo localizado se conserva `assignment=disponible` con custodio null o `assignment=asignado` con custodio presente. En No localizado o Baja la asignación actual es null y el custodio actual es null; los últimos valores conocidos pertenecen al snapshot del evento. La migración de 004 debe reemplazar `asset_custody_consistent` para incluir estas alternativas, no solo añadir una columna lifecycle.

El vocabulario LOCATED/UNLOCATED/RETIRED de diseño se serializa como `localizado`/`no_localizado`/`baja`. Los registros existentes migran a localizado conservando su asignación/custodia. Los filtros actuales siguen aceptando disponible/asignado; nunca presentan No localizado/Baja como disponible. Los servicios de entrega, devolución, condición y rectificación vuelven a validar localización y mantenimiento cuando corresponda.

## Decisiones concurrentes

Solicitud, decisión, recuperación, reasignación, cambio de facultad y desactivación usan un orden de bloqueos documentado por el implementador y verifican estado/permisos dentro de la transacción. La recuperación y aprobación compiten sobre el mismo activo: solo una transición válida se confirma; la otra devuelve conflicto y no crea eventos parciales. Revisores activos, facultad distinta y autor distinto se verifican al asignar y al decidir. Cualquier actualización de la facultad de una cuenta revisora debe rechazar cambios que vuelvan inelegibles sus solicitudes pendientes, hasta reasignarlas por operador.

## Importación

Preview no crea activos, documentos ni lotes de licencia. Guarda contenido normalizado inmutable suficiente para ejecutar el lote, con propietario y hash. Ambas confirmaciones pertenecen al Gestor propietario. Al aplicar se revalidan referencias, unicidad y permisos contra la DB actual, pues podrían cambiar desde la vista previa. Un conflicto revierte todas las escrituras.

Aplicación repetida de un lote APPLIED por su propietario devuelve HTTP 200 con el resultado anterior. Primera aplicación devuelve 201; estados vencido/cancelado/no confirmado devuelven 409. El batch se bloquea para impedir aplicaciones simultáneas duplicadas. La expiración elimina contenido temporal; el resumen mínimo de aplicación se conserva para la idempotencia según el plazo técnico documentado en T002 de 008. Las secuencias PostgreSQL pueden dejar huecos tras rollback; jamás se reutiliza código TI ni se exige numeración sin huecos.

## Proyecciones y evidencia inmutable

Asset, MaintenanceEvent, Incident y DecommissionRequest pueden actualizar su estado actual por servicios transaccionales. Cada transición crea además evidencia append-only con antes/después, autor, tiempo y revisión; «append-only» se aplica a esa evidencia y a Movement, no impide mantener una proyección del estado vigente. No se sobrescribe el reporte original al resolver/recuperar ni la asignación anterior al reasignar.

Solicitud y decisión conservan identificadores y nombres de facultades/revisores al momento de la operación, además de referencias actuales; los cambios de catálogo o perfil no reescriben esos snapshots. La API calcula rectifiable_movement_id usando revisión global, no solo el último id de Movement; devuelve null si existe cualquier evento posterior que impida rectificar.
