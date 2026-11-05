# Modelo de datos: fichas y adquisición

## Faculty

- id estable; name obligatorio y único normalizado; active.
- Los activos y revisores referencian Faculty.
- Una facultad referenciada no se borra físicamente.

## AcquisitionDocument

- id; source: PURCHASE o DONATION; reference; document_date; supplier (solo compra); invoice_total (solo compra); support_type (donación; junto con reference); created_by; created_at.
- PURCHASE requiere referencia, fecha, proveedor y total USD.
- DONATION requiere reference y support_type textuales; no se almacena un archivo.
- No contiene binario ni imagen.

## AcquisitionLine

- document; asset (OneToOne); item_value USD; acquired_on; date_unknown_reason.
- Para PURCHASE item_value es importe por equipo en la factura.
- Para DONATION item_value es valor estimado individual.
- Un documento puede asociarse a muchos activos; un activo tiene un registro de adquisición vigente.
- Cambios quedan auditados; la política de revisión de documento existente es apéndice de la auditoría.

## Asset metadata audit

- asset, actor, created_at, reason, before_json, after_json.
- Campos descriptivos y adquisición. La facultad usa exclusivamente AssetFacultyChange y permiso Operador.
- No reemplaza movimientos de condición, asignación, custodio o ubicación.

## Custodian profile audit

- custodian, actor, created_at, before_json, after_json.
- Movimientos antiguos consultan snapshot inmutable de nombre/correo del momento del movimiento.

## Fecha de adquisición en AcquisitionLine

- acquired_on nullable solamente si date_unknown_reason está presente.
- Moneda USD se centraliza en configuración del backend; persistir importes en decimal, sin formato localizado en DB.
## Auditoría de facultad responsable

`AssetFacultyChange`: activo, facultad anterior/nueva, motivo obligatorio, operador autor y fecha/hora del servidor. El cambio se realiza con bloqueo transaccional del activo. La integración 005 impide el cambio mientras una solicitud de baja esté pendiente.

## Aclaraciones confirmadas por Alex — 2026-11-04

- Fecha y motivo residen en AcquisitionLine, conforme al plan.
- Donación usa support_type + reference en la API de 003. El CSV de 008 usa actualmente support_description; su adaptación queda pendiente, sin inferir equivalencias de textos históricos.
- Cada corrección de documento genera AcquisitionDocumentChange y un AssetChange por activo afectado, atómicamente. Los AssetChange guardan resulting_revision y snapshots del documento con currency. El evento del documento conserva antes/después aun si todavía no tiene activos.
- La relación Asset.faculty y las protecciones SQL se incorporarán en T004 con migración revisable; no están activadas por la preparación de modelos T003.


## Integridad preparada, todavía sin esquema — 2026-11-04

Los textos obligatorios usan CHECK de contenido no blanco. AssetChange y AssetFacultyChange declaran revisión positiva y única por activo dentro de cada tabla; T006 debe mantener la revisión global bajo bloqueo, incluyendo movimientos y las demás auditorías. Evidencia solo insertable por ORM; protección SQL append-only y contra borrado de dominio pendiente T004. No se afirma que estos constraints estén instalados.

Persisten decisiones funcionales pendientes listadas en integration-notes.md: signo/cero monetario, adaptación CSV de respaldo, fecha documental de donación, cambios de origen con líneas y concurrencia documental aún no especificada. No inferir aprobación a partir de la nulabilidad/campos del modelo provisional.


## Esquema de expansión preparado — 2026-11-04

Asset.faculty: FK Faculty con PROTECT, null=True y blank=True temporalmente, sin default. Esta nulabilidad conserva el alta de 002 durante la transición; no sustituye el requisito final de facultad obligatoria. La migración 0004 crea entidades, FK/OneToOne y constraints, sin filas de dominio.

En PostgreSQL temporal se verificaron constraints instalados y triggers de conservación; nueve CHECK de textos de tablas legadas quedan NOT VALID para no modificar/rechazar su contenido anterior al expandir. Auditoría append-only por UPDATE/DELETE y dominio sin DELETE incluso sin referencias; TRUNCATE/DROP privilegiados no cubiertos. No se declara migrada la base local, mapeado el legado ni completada T004.

## CustodianChange T014 sin cambio de esquema — 2026-11-04

Confirmación humana: concurrencia de perfil mediante expected_profile bajo lock; motivo guardado en after_json junto al perfil nuevo, perfil anterior en before_json. Actor/created_at existentes conservan autoría y fecha. No hay revisión propia de Custodian ni revisión nueva de activos; no se añade columna ni migración. El CAS compara valores actuales: no es un contador monotónico y no detecta un ciclo A→B→A. Un contador o token persistente exigiría un contrato/esquema posterior aprobado.

## Estado vigente de esquema y revisión documental — 2026-11-04

El grafo activo sigue en 0004_acquisition_expansion; ninguna nueva migración activa y ninguna aplicación local. Plantilla de contracción fuera del grafo, con pruebas de datos históricos. Se conserva Asset.faculty nullable hasta transición revisada.

Edición compartida usa expected_document con source/reference/document_date/supplier/invoice_total/support_type/currency y expected_revisions con todos los ids actuales. Cada AssetChange conserva el snapshot completo de adquisición y resulting_revision, mientras AcquisitionDocumentChange conserva metadatos anteriores/nuevos y motivo. asset_revision es un campo readonly de salida de líneas para obtener las revisiones consultadas; no es una columna nueva ni una revisión controlada por el cliente.
