# Requisitos funcionales del inventario

Base develop cbb632d. Los identificadores se componen del módulo y del FR correspondiente en su especificación. El texto procede de las especificaciones existentes.

## 002-registro-consulta-activos

Fuente: [u1-integracion/specs/002-registro-consulta-activos/spec.md](../../specs/002-registro-consulta-activos/spec.md)

| ID | Requisito |
| --- | --- |
| 002/FR-001 | permitir registrar y consultar activos físicos, registrar entregas y devoluciones, rectificar movimientos, cambiar la condición de activos Disponibles y consultar su historial mediante pantalla web y API. La entrega incluirá pruebas de las funcionalidades acordadas. |
| 002/FR-002 | generar automáticamente un código de inventario único y estable con prefijo `TI-` y numeración creciente, presentada como `TI-000001`, `TI-000002`, etc. La numeración no se reinicia por año ni categoría y no se reutilizan códigos. |
| 002/FR-003 | conservar nombre y descripción como campos separados, además de categoría, marca, modelo, número de serie, ubicación y custodio. |
| 002/FR-004 | exigir nombre, descripción, categoría, marca, modelo, número de serie y ubicación al registrar el activo. El custodio representa a la persona que tiene la custodia temporal; no se exige ni se asigna custodio temporal al dar de alta el activo o después de una devolución. |
| 002/FR-005 | exigir los dos campos separados: condición (`Operativo`, `Averiado` o `En reparación`) y asignación (`Disponible` o `Asignado`). Al dar de alta se establece Disponible; esto no implica que su condición sea Operativo. |
| 002/FR-006 | utilizar las categorías confirmadas: computadora de escritorio, portátil, monitor, impresora, equipo de red y periférico. |
| 002/FR-007 | rechazar un activo duplicado por la combinación marca + modelo + serie, comparando los tres campos sin distinguir mayúsculas y eliminando espacios al principio y al final. Conservar los caracteres internos de la serie: ABC-123 y ABC123 son distintos. La serie por sí sola no se establece como identificador único global. |
| 002/FR-008 | permitir ver el listado de activos y la ficha individual de cada equipo registrado. |
| 002/FR-009 | permitir buscar por coincidencia parcial sin distinguir mayúsculas en al menos uno de estos campos: código, nombre del activo, marca, modelo, serie y nombre/correo del custodio actual. Permitir filtrar por categoría, condición, asignación, ubicación y custodio actual; cada resultado debe satisfacer la búsqueda y todos los filtros seleccionados. |
| 002/FR-010 | restringir el acceso a la aplicación y sus operaciones a gestores identificados y autorizados. Los custodios se registran como personas sin cuenta de acceso en este incremento. Todos los gestores autorizados tienen los mismos permisos sobre el inventario completo: registrar activos y custodios, consultar, entregar, devolver, cambiar condición y rectificar movimientos elegibles, incluso si los registró otro gestor. |
| 002/FR-011 | distinguir al gestor que registra operaciones del custodio temporal del activo. Distintos gestores autorizados pueden gestionar los activos; no se fija un gestor responsable único por activo. |
| 002/FR-012 | permitir una entrega únicamente si el activo está Disponible y Operativo; la entrega lo deja Asignado a un custodio temporal identificado y conserva el gestor autor del movimiento. |
| 002/FR-013 | rechazar devoluciones sin entrega activa. Al registrar una devolución válida, exigir que el gestor indique la condición de recepción entre Operativo, Averiado y En reparación; dejar el activo Disponible y sin custodio temporal; conservar el antecedente, el autor y las condiciones anterior y recibida en el historial. |
| 002/FR-014 | conservar y consultar en cada movimiento el activo, tipo de operación, fecha y hora de registro generadas automáticamente, gestor autor, custodio relacionado y condiciones anterior y posterior, además de una observación opcional escrita por el gestor. El autor corresponde al gestor que realiza la operación; no es una persona elegida para sustituir a quien la registra. |
| 002/FR-015 | dar de alta todos los activos como Disponible y sin custodio temporal. Cualquier custodia temporal posterior se inicia mediante una entrega registrada; no se permite un alta directamente Asignada en este incremento. |
| 002/FR-016 | conservar sin reescritura ni borrado el movimiento original cuando se corrija un error; añadir una rectificación vinculada con motivo obligatorio, gestor autor y fecha/hora que anule su efecto y restaure la situación anterior. La operación correcta se registra después como una nueva operación separada; la rectificación no edita directamente los datos originales. |
| 002/FR-017 | permitir rectificar únicamente la última entrega, devolución o cambio de condición vigente de cada activo, sin operaciones posteriores. Rechazar movimientos con operaciones posteriores, ya rectificados y las propias rectificaciones. Anular el último movimiento no habilita la rectificación de movimientos anteriores. |
| 002/FR-018 | permitir Cambiar condición únicamente sobre activos Disponibles, eligiendo otra de las condiciones admitidas y exigiendo motivo. Conservar el cambio, su autor, fecha/hora y condiciones anterior/posterior en el historial. Esta operación representa un cambio real y no sustituye la rectificación de un registro erróneo. |
| 002/FR-019 | identificar a cada custodio con nombre completo y correo institucional obligatorios y dependencia opcional. El correo es único entre custodios comparándolo sin distinguir mayúsculas y eliminando espacios exteriores; la persona no recibe una cuenta de acceso. Validar el formato del correo sin restringir el dominio en este incremento. |
| 002/FR-020 | conservar la ubicación actual informada del activo; exigir y registrar la ubicación de destino en la entrega y el lugar de recepción en la devolución, actualizando la ficha y conservando esos lugares en los movimientos correspondientes. La rectificación restaura también la ubicación anterior si el movimiento anulado la cambió. |
| 002/FR-021 | permitir introducir marca, modelo y ubicación como texto; no incorporar catálogos administrables para esos tres datos en este incremento. Se mantienen las categorías y los valores de condición/asignación ya confirmados. |
| 002/FR-022 | conservar todo el historial de este incremento sin borrado automático. Los plazos institucionales de conservación se definirán en una etapa posterior, sin inventar una política institucional en este trabajo. |
| 002/FR-023 | mantener las reglas de identidad y estado también ante solicitudes simultáneas: no crear duplicados, repetir códigos ni aceptar doble entrega, devolución o rectificación incompatible. Una operación rechazada no deja cambios parciales ni un movimiento válido. |

## 003-fichas-adquisiciones

Fuente: [u1-integracion/specs/003-fichas-adquisiciones/spec.md](../../specs/003-fichas-adquisiciones/spec.md)

| ID | Requisito |
| --- | --- |
| 003/FR-001 | El sistema MUST conservar los datos base de activo y custodio definidos en 002 y permitir editar los campos descriptivos acordados. |
| 003/FR-002 | Toda edición de datos de activo MUST exigir motivo y conservar antes/después, actor y fecha/hora. |
| 003/FR-003 | El sistema MUST preservar la representación histórica del custodio en movimientos previos después de corregir su ficha. |
| 003/FR-004 | Una edición general MUST rechazar cambios de ubicación, condición, asignación, custodio actual y situación de baja/no localizado. |
| 003/FR-005 | El operador técnico MUST crear, consultar y actualizar la lista manual de facultades sin sincronización institucional. |
| 003/FR-006 | Cada activo MUST referenciar una facultad responsable existente. |
| 003/FR-007 | El sistema MUST representar adquisición de activos como compra o donación. |
| 003/FR-008 | Una compra MUST registrar referencia, fecha y proveedor de factura, total en USD, y líneas de activo con importe individual. |
| 003/FR-009 | Una donación MUST registrar referencia textual de respaldo y valor estimado individual por activo; un documento podrá enlazarse a varios activos. |
| 003/FR-010 | La fecha de adquisición MUST registrarse o marcarse desconocida con motivo obligatorio. |
| 003/FR-011 | Los documentos de adquisición MUST admitir asociación con varios activos y conservar total común e importes individuales donde correspondan. |
| 003/FR-012 | El importe monetario MUST usar USD mediante una constante/configuración única del backend; no habrá selector de moneda en interfaz. |
| 003/FR-013 | La edición de custodio MUST preservar historia de movimientos y registrar autor, fecha/hora y antes/después del perfil. |
| 003/FR-014 | El sistema MUST rechazar una edición que cree una duplicidad de identidad de activo según la regla marca+modelo+serie de 002. |
| 003/FR-015 | El sistema MUST evitar borrado físico de documentos, activos, facultades referenciadas y auditoría. |
| 003/FR-016 | Solo el operador MUST cambiar la facultad responsable; cada cambio exige motivo y auditoría antes/después. Si hay solicitud de baja pendiente, debe rechazarse (integración con 005). |

## 004-novedades-mantenimiento

Fuente: [u1-integracion/specs/004-novedades-mantenimiento/spec.md](../../specs/004-novedades-mantenimiento/spec.md)

| ID | Requisito |
| --- | --- |
| 004/FR-001 | Registrar novedad por daño/observación con descripción, tipo, fecha/hora y gestor autor. |
| 004/FR-002 | Permitir novedad de daño/observación en activo Disponible o Asignado y mostrar alerta hasta su resolución. |
| 004/FR-003 | Resolver novedad con nota obligatoria, gestor y fecha/hora; conservarla en el historial. |
| 004/FR-004 | No cambiar condición automáticamente por una novedad; usar el flujo de condición existente para cambios reales. |
| 004/FR-005 | Iniciar mantenimiento para activo localizado, Disponible, sin custodia actual y sin otro mantenimiento En curso. |
| 004/FR-006 | Guardar al inicio descripción, ubicación/taller, autor, fecha/hora y ubicación previa. |
| 004/FR-007 | Bloquear entregas mientras exista mantenimiento En curso, aunque la condición sea Operativo. |
| 004/FR-008 | Cerrar mantenimiento exigiendo resultado y ubicación de recepción; proponer ubicación previa y solicitar confirmación explícita antes de guardar. |
| 004/FR-009 | Mantener separado el evento de mantenimiento del cambio de condición. |
| 004/FR-010 | Registrar pérdida/robo con tipo, descripción, autor, fecha/hora y snapshots de ubicación, condición, asignación, custodio y mantenimiento previo. |
| 004/FR-011 | Cambiar situación del activo a No localizado; bloquear entrega, devolución como si estuviera físicamente presente y cierre normal de mantenimiento. |
| 004/FR-012 | Al reportar No localizado durante mantenimiento, marcar dicho evento Interrumpido por No localizado, sin resultado. Al recuperar, cualquier continuación usa un evento nuevo. |
| 004/FR-013 | Registrar recuperación con condición y ubicación nuevas, conservar código e historial y dejar Disponible/sin custodio vigente. |
| 004/FR-014 | No dar de baja automáticamente un activo No localizado. |
| 004/FR-015 | Preservar eventos originales y resolver conflictos concurrentes sin cambios parciales. |
| 004/FR-016 | Conservar toda novedad, mantenimiento, reporte y recuperación sin borrado automático. |

## 005-bajas-aprobacion

Fuente: [u1-integracion/specs/005-bajas-aprobacion/spec.md](../../specs/005-bajas-aprobacion/spec.md)

| ID | Requisito |
| --- | --- |
| 005/FR-001 | Permitir baja normal solo para activo localizado, Disponible, sin custodio vigente y sin mantenimiento En Curso. |
| 005/FR-002 | Permitir baja normal bajo cualquier condición; exigir motivo y guardar autor/fecha. |
| 005/FR-003 | Antes de la baja normal de un activo en mantenimiento, exigir cierre del mantenimiento con resultado. |
| 005/FR-004 | Conservar ficha, historial y código; no borrar activo ni reutilizar su identificador. |
| 005/FR-005 | Permitir solicitar baja solo a activo No localizado, con motivo, usuario Gestor, fecha y revisor asignado. |
| 005/FR-006 | Rechazar autoaprobación y revisores cuya facultad sea igual a la responsable del activo. |
| 005/FR-007 | Limitar cada revisor a solicitudes asignadas y datos del activo necesarios para decidir; no conceder acceso de edición/inventario. |
| 005/FR-008 | Aprobar baja No localizado mediante decisión inmutable con autor/fecha; al aprobar el activo pasa a Baja. |
| 005/FR-009 | Rechazar solicitud con motivo obligatorio; el activo continúa No localizado y admite nueva solicitud con motivo actualizado. |
| 005/FR-010 | Cancelar automáticamente solicitud pendiente si el activo se recupera; guardar motivo, autor del evento automático, fecha y vínculo a recuperación. |
| 005/FR-011 | Solo el operador puede reasignar una solicitud pendiente a otro revisor elegible; impedir desactivar revisor hasta que el operador reasigne todas las pendientes. |
| 005/FR-012 | Operador técnico autorizado puede crear/desactivar revisores desde la interfaz y asignar facultad. |
| 005/FR-013 | El primer inicio de sesión del revisor exige cambiar la contraseña temporal. |
| 005/FR-014 | Alta/baja de gestores permanece por comandos locales; usuario inactivo no accede y la autoría histórica se conserva. |
| 005/FR-015 | Permitir rectificar una baja errónea solo si es el error más reciente, con motivo y vínculo, preservando baja original. |
| 005/FR-016 | Mantener los datos e historial sin borrado automático. |
| 005/FR-017 | Rechazar el cambio de facultad responsable mientras exista solicitud de baja pendiente; la autorización y auditoría del cambio corresponden a 003. |

## 006-lotes-licencias

Fuente: [u1-integracion/specs/006-lotes-licencias/spec.md](../../specs/006-lotes-licencias/spec.md)

| ID | Requisito |
| --- | --- |
| 006/FR-001 | Registrar y consultar lotes de licencia de software sin asociarlos individualmente a activos/personas. |
| 006/FR-002 | Registrar producto, proveedor y modalidad de puestos finitos por usuario o dispositivo. |
| 006/FR-003 | Registrar cantidad comprada y cantidad en uso como enteros no negativos. |
| 006/FR-004 | Calcular remanentes = compradas − en uso; rechazar cantidad en uso > compradas. |
| 006/FR-005 | Exigir fecha de inicio de vigencia; fecha de fin opcional. |
| 006/FR-006 | Derivar estado Por iniciar/Vigente/Vencido a partir de fechas, sin borrar el lote. |
| 006/FR-007 | Mostrar remanentes aun si está vencido y distinguirlos de disponibilidad vigente. |
| 006/FR-008 | Permitir edición auditada de los campos de lote y cantidades; preservar autor, fecha/hora y antes/después. |
| 006/FR-009 | No guardar claves de activación, licencias ilimitadas/de campus o asignaciones individuales. |
| 006/FR-010 | Gestores autorizados tienen mismos permisos; operaciones sujetas a sesión, CSRF y validación del servidor. |
| 006/FR-011 | El listado permite buscar producto/proveedor y filtrar tipo/estado para localizar el lote. |
| 006/FR-012 | No relacionar una licencia con el registro de adquisición de activos físicos en este alcance. |

## 007-qr-activos

Fuente: [u1-integracion/specs/007-qr-activos/spec.md](../../specs/007-qr-activos/spec.md)

| ID | Requisito |
| --- | --- |
| 007/FR-001 | generar enlace interno con código TI y sin datos personales. |
| 007/FR-002 | descargar QR SVG imprimible para un activo físico. |
| 007/FR-003 | preservar destino interno tras login y rechazar redirecciones externas arbitrarias. |
| 007/FR-004 | requerir autenticación y permiso Gestor antes de mostrar la ficha. |
| 007/FR-005 | responder sin revelar datos cuando el código no existe. |
| 007/FR-006 | construir URL desde `PUBLIC_APP_URL` configurada, no desde Host no confiable. |
| 007/FR-007 | regenerar QR bajo demanda sin persistir imagen; no crear QR para licencias. |
| 007/FR-008 | mantener acceso protegido en cualquier estado del activo. |

## 008-importacion-csv

Fuente: [u1-integracion/specs/008-importacion-csv/spec.md](../../specs/008-importacion-csv/spec.md)

| ID | Requisito |
| --- | --- |
| 008/FR-001 | aceptar CSV de activos físicos y lotes de licencias mediante plantillas separadas y versionadas. |
| 008/FR-002 | validar el archivo completo y mostrar todos los errores por fila/campo antes de escribir datos. |
| 008/FR-003 | ante cualquier error, rechazar el lote entero y crear cero registros de dominio. |
| 008/FR-004 | presentar una vista previa completa y resumen de los registros válidos. |
| 008/FR-005 | exigir dos confirmaciones explícitas del mismo Gestor que inició el lote. |
| 008/FR-006 | vincular confirmaciones a una vista previa inmutable identificada por lote/hash. |
| 008/FR-007 | aplicar activos o lotes en una transacción atómica, sin resultados parciales. |
| 008/FR-008 | generar código TI en servidor y crear activos importados como Disponibles/sin custodio. |
| 008/FR-009 | respetar reglas de adquisición de compra/donación y documentos compartidos de 003. |
| 008/FR-010 | tratar cada fila de licencias como un lote, aplicando reglas de fecha y cantidad de 006. |
| 008/FR-011 | hacer idempotente el reintento de aplicación del mismo lote ya aplicado. |
| 008/FR-012 | rechazar archivo que exceda límites técnicos configurados; nunca truncar ni importar parcialmente. |
