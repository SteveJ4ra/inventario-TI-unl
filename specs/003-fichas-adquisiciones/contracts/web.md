# Contratos web: fichas y adquisición

- Gestor: crear/editar ficha, elegir facultad, indicar compra o donación y completar el documento común más líneas individuales.
- Cuando una factura/documento tenga varios activos, el flujo permite enlazar varios y asignar valor individual a cada uno.
- Para fecha de adquisición desconocida, se habilita el campo de motivo; sin motivo no se guarda.
- Edición general muestra motivo requerido y diferencias antes/después confirmables; ubicación, condición y asignación se editan desde su operación dedicada.
- Edición de custodio muestra nombre, correo y dependencia; la ficha nueva no cambia snapshots históricos.
- Operador: pantalla de mantenimiento manual de facultades; no sincroniza con sistemas institucionales.
- Montos se presentan como USD; la UI no contiene selector de moneda.
- Los errores se muestran junto al campo y la vista de ficha muestra historial de cambios.

La selección de facultad por Gestor corresponde solo al alta. La edición posterior se ofrece únicamente al Operador, con motivo y diferencias antes/después; 005 bloquea si existe solicitud pendiente. Registrar primero metadatos de factura/respaldo y reutilizar su id al crear activos; no pedir ids de activos inexistentes.

### Compra con activos existentes: confirmación humana 2026-11-04

Al crear una factura se pueden consultar fichas existentes, revisar código y revisión, y preparar varias asociaciones con valor, motivo auditado y fecha o motivo de desconocimiento. La lista no escribe hasta guardar la factura; el envío es único y atómico. Se impiden duplicados y fichas con adquisición vigente. Ante conflicto se conserva la entrada y el Gestor debe consultar nuevamente la ficha; no se actualiza la revisión ni se reintenta automáticamente. El alta posterior de activos nuevos sigue reutilizando el id del documento guardado.

### Donaciones T012 — 2026-11-04

Registrar donación abre el mismo AcquisitionForm con source=DONATION: tipo y referencia textuales, sin proveedor, total ni fecha documental. Permite crear/cargar respaldo y registrar varios activos nuevos con valor estimado individual, facultad y fecha/motivo. También permite preparar asociaciones iniciales de activos existentes según la confirmación humana, enviando estimated_value y la revisión consultada. Los formularios de compra y donación conservan su estado separado al ocultarse dentro de la sesión y se descartan al salir. Un documento del tipo contrario se rechaza en la selección, sin convertirlo. La ficha presenta tipo/referencia, valor estimado y fecha/motivo; no presenta un total de factura de donación.

Los errores conservan entrada, asociaciones y documento confirmado; no hay reintentos automáticos ni éxito ante respuesta incierta. La fecha documental y la política monetaria siguen pendientes; no se incluyen controles para decidirlas en la UI.

### Edición y facultades T014–T017 — 2026-11-04

Gestor: Editar ficha permite revisar diferencias descriptivas y de la línea existente, indicar motivo y confirmar con la revisión consultada; no muestra controles de facultad, ubicación, condición ni custodia. Un conflicto conserva el borrador y no reintenta ni cambia revisión automáticamente. Recargar ficha es una acción explícita del usuario. Editar custodios permite elegir perfil, corregir nombre/correo/dependencia, revisar diferencias y enviar reason + expected_profile confirmado por Alex; no cambia movimientos previos.

Operador: Administrar facultades consulta también las inactivas, crea y corrige nombre/estado con confirmación de diferencias. La cuenta solo Operador no consulta inventario ordinario ni muestra alta de activos. El cambio de facultad de un activo se presenta como no disponible mientras falte el guard real 005; no hay éxito simulado ni formulario que eluda esa protección. La selección inicial de facultad sigue en las altas de compra/donación.

El historial de ficha consume la envoltura combinada y presenta antes/después, motivo, autor y revisión; conserva la representación original de movimientos y rectificaciones. Si falla la consulta combinada, se informa expresamente y se presentan únicamente los movimientos obtenidos por la ruta 002, sin afirmar historial completo.

### Estado vigente del documento compartido — 2026-11-04

Editar documento compartido consulta primero el documento actual y sus revisiones readonly, presenta los campos del origen vigente y diferencias confirmables, y envía snapshot completo/mapa de revisiones/motivo. Conflicto conserva borrador sin rebase ni reintento automático. No hay control de cambio de origen, moneda ni fecha documental de donación. Tras éxito se actualizan la ficha y el historial consultados. Cuentas con ambos permisos explícitos pueden abrir el catálogo y volver al inventario; ser Operador por sí solo no concede Gestor.
