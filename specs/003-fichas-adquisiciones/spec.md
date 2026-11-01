# Especificación: administración de fichas y adquisición

**Rama propuesta:** feature/alex-003-fichas-adquisiciones
**Identificador:** 003-fichas-adquisiciones
**Creado:** 1 de noviembre de 2026
**Estado:** especificación preparada; no implementada.
**Base:** incremento 002 y decisiones DBE-001 a DBE-011 y DBE-048, DBE-050 en ../../docs/sdd/decisiones-alcance-backend.md.

## Descripción

Permitir mantener datos descriptivos correctos de activos y custodios, identificar la facultad responsable del activo y documentar su adquisición mediante compra o donación. La compra y la donación pueden usar un documento compartido por varios activos; cada activo conserva su propio importe o valor estimado. Los cambios preservan auditoría.

## Actores

- Gestor: registra y edita activos y custodios, consulta historial.
- Operador técnico: mantiene la lista manual de facultades.
- Custodio: persona registrada, sin acceso al sistema.

## Historias y aceptación

### US1 — Documentar compras de activos (P1)

Como gestor, quiero asociar uno o más activos a una factura para conservar el documento común y el valor individual de cada equipo.

**Prueba independiente:** crear una factura ficticia y dos activos asociados; consultar total común y valores por activo.

1. Dada una compra, al guardar el documento se exige referencia, fecha de factura, proveedor y total en USD.
2. Dada una factura con varios equipos, cada línea enlaza un activo y su valor individual; la factura mantiene un único total compartido.
3. Dado un activo nuevo, se registra fecha de adquisición; si se desconoce, el gestor registra el motivo y no inventa una fecha.
4. Dada una factura, el documento no almacena una imagen ni archivo adjunto en este incremento.

### US2 — Registrar donaciones de activos (P1)

Como gestor, quiero asociar el respaldo textual de una donación a uno o más equipos y registrar el valor estimado individual de cada uno.

**Prueba independiente:** registrar un acta ficticia compartida por dos activos y consultar su referencia y valores.

1. Una donación conserva tipo y referencia del respaldo, y valor estimado por cada activo.
2. El mismo respaldo puede asociarse con varios activos sin duplicar su identidad como documento.
3. La donación no requiere una factura inexistente ni almacenamiento de imágenes.

### US3 — Corregir datos de activos, custodios y facultades (P1)

Como gestor, quiero corregir información descriptiva conservando quién cambió qué y cuándo.

**Prueba independiente:** editar ficha y persona custodio ficticias; consultar valores actuales y antecedentes.

1. La edición de activo exige motivo y conserva autor, fecha/hora y valores anteriores/nuevos.
2. Ubicación, condición, asignación, custodia y baja no se cambian mediante edición general; se usan sus operaciones de ciclo de vida.
3. Editar un custodio no reescribe los datos personales que fueron capturados en movimientos anteriores.
4. La edición del custodio conserva el valor previo/nuevo, autor y fecha/hora.
5. El operador puede mantener una lista manual de facultades. Cada activo identifica su facultad responsable.
6. Solo el operador puede cambiar la facultad responsable de un activo; el cambio exige motivo y conserva autor, fecha y valores anterior/nuevo.
7. El cambio de facultad se rechaza si existe una solicitud de baja pendiente, regla integrada con 005.

## Requisitos funcionales

- FR-001: El sistema MUST conservar los datos base de activo y custodio definidos en 002 y permitir editar los campos descriptivos acordados.
- FR-002: Toda edición de datos de activo MUST exigir motivo y conservar antes/después, actor y fecha/hora.
- FR-003: El sistema MUST preservar la representación histórica del custodio en movimientos previos después de corregir su ficha.
- FR-004: Una edición general MUST rechazar cambios de ubicación, condición, asignación, custodio actual y situación de baja/no localizado.
- FR-005: El operador técnico MUST crear, consultar y actualizar la lista manual de facultades sin sincronización institucional.
- FR-006: Cada activo MUST referenciar una facultad responsable existente.
- FR-007: El sistema MUST representar adquisición de activos como compra o donación.
- FR-008: Una compra MUST registrar referencia, fecha y proveedor de factura, total en USD, y líneas de activo con importe individual.
- FR-009: Una donación MUST registrar referencia textual de respaldo y valor estimado individual por activo; un documento podrá enlazarse a varios activos.
- FR-010: La fecha de adquisición MUST registrarse o marcarse desconocida con motivo obligatorio.
- FR-011: Los documentos de adquisición MUST admitir asociación con varios activos y conservar total común e importes individuales donde correspondan.
- FR-012: El importe monetario MUST usar USD mediante una constante/configuración única del backend; no habrá selector de moneda en interfaz.
- FR-013: La edición de custodio MUST preservar historia de movimientos y registrar autor, fecha/hora y antes/después del perfil.
- FR-014: El sistema MUST rechazar una edición que cree una duplicidad de identidad de activo según la regla marca+modelo+serie de 002.
- FR-015: El sistema MUST evitar borrado físico de documentos, activos, facultades referenciadas y auditoría.
- FR-016: Solo el operador MUST cambiar la facultad responsable; cada cambio exige motivo y auditoría antes/después. Si hay solicitud de baja pendiente, debe rechazarse (integración con 005).

## Criterios de éxito

- SC-001: Una factura puede enlazar varios activos y cada uno muestra su importe individual sin duplicar el total común.
- SC-002: Una donación enlaza un documento de respaldo compartido y conserva valoración separada por activo.
- SC-003: Una fecha de adquisición desconocida requiere motivo; una fecha inventada no aparece.
- SC-004: La edición no altera movimientos antiguos y permite consultar el antes/después de cada cambio.
- SC-005: Un activo con facultad responsable válida puede usarse después en la regla de revisor de otra facultad.
- SC-006: Un gestor no puede cambiar la facultad; el operador puede hacerlo con motivo e historial, excepto durante una solicitud de baja pendiente.

## Límites

No se incorporan compras, presupuesto, contabilidad, carga de facturas, adjuntos, OCR, transferencias entre unidades ni integración universitaria. La lista de facultades se administra manualmente. Los nombres iniciales de facultades los cargará el operador autorizado.
