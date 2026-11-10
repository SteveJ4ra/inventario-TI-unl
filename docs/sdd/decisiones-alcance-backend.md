# Registro de decisiones: alcance ampliado del backend

**Fecha:** 1 de noviembre de 2026 (America/Guayaquil).
**Fuente:** respuestas explícitas de Steven para preparar los incrementos backend posteriores a 002.
**Estado:** decisiones funcionales aceptadas para el proyecto académico; no son políticas institucionales aprobadas.

## Activos, adquisiciones y custodios

| ID | Decisión |
|---|---|
| DBE-001 | La meta es preparar el SDD del backend completo y después dividir el trabajo entre seis integrantes; no ampliar el producto con extras no justificados. |
| DBE-002 | Se conservan las seis categorías físicas de 002. No se añaden categorías por ejemplos. |
| DBE-003 | Se permiten correcciones auditadas a los datos descriptivos de activos; no se cambia ubicación, condición, asignación ni ciclo de vida por una edición general. Las ediciones de activos registran autor, fecha, motivo y antes/después. |
| DBE-004 | Se pueden corregir nombre, correo y dependencia del custodio; el historial previo conserva los datos que tenía cuando ocurrió cada movimiento. Los custodios siguen sin cuenta de acceso. |
| DBE-005 | El activo registra facultad responsable para aplicar la separación de facultades en una baja de No localizado. La lista es manual, administrada por un operador técnico y no sincronizada con servicios de la UNL. |
| DBE-006 | La adquisición de un activo se clasifica como compra o donación en este alcance. |
| DBE-007 | Una compra exige datos textuales de factura: referencia/número, fecha, proveedor y total. Un mismo documento de compra puede asociarse a varios activos. |
| DBE-008 | Cada activo asociado a una factura conserva su valor individual según el detalle del documento; la factura compartida conserva el total común. |
| DBE-009 | Una donación conserva respaldo documental textual y valor estimado individual; un documento de respaldo puede compartirse entre varios activos. No se guardan imágenes o archivos de esos documentos en esta entrega. |
| DBE-010 | La fecha de adquisición puede declararse desconocida solo acompañada de un motivo; no se inventa una fecha. |
| DBE-011 | Los importes se expresan en USD. La moneda se define en un único punto de configuración del backend; la interfaz no permite cambiarla. Una conversión futura requeriría un cambio de código y su validación. |

## Novedades, mantenimiento y situación del activo

| ID | Decisión |
|---|---|
| DBE-012 | Una novedad permite registrar daño u observación aun cuando el activo esté asignado. La novedad guarda descripción, autor y fecha; una alerta permanece mientras esté pendiente. |
| DBE-013 | Una novedad por daño no cambia automáticamente la condición. Si el funcionamiento está afectado, la condición se cambia mediante la operación correspondiente cuando sea elegible. |
| DBE-014 | Al resolver una novedad se exige nota de resolución y se guardan fecha y gestor; el antecedente permanece consultable. |
| DBE-015 | Pérdida y robo son tipos de novedad distintos de daño o avería. |
| DBE-016 | El reporte de pérdida/robo marca el activo No localizado, bloquea nuevas entregas y conserva como último estado conocido asignación, condición, ubicación, custodio y mantenimiento, si aplica. No crea una devolución ficticia ni una baja automática. |
| DBE-017 | Un activo recuperado conserva el mismo registro/código; se registra recuperación, revisión, condición y ubicación y queda Disponible/sin custodio. |
| DBE-018 | El mantenimiento se registra al iniciar: fecha, descripción y ubicación/taller; queda En curso. Todo mantenimiento en curso bloquea entregas aunque la condición siga Operativa. |
| DBE-019 | El cierre registra fecha y resultado. El gestor cambia la condición aparte cuando corresponde; mantenimiento no agenda trabajos futuros. |
| DBE-020 | Si el activo pasa a No localizado durante un mantenimiento, este queda Interrumpido por No localizado sin resultado de reparación. Si se recupera, se crea un mantenimiento nuevo para continuar. |
| DBE-021 | Un reporte No localizado conserva el estado previo aunque se pierda/robe mientras estaba Disponible, Asignado o En mantenimiento; la ficha actual deja de afirmar que está bajo custodia vigente. |

## Bajas y aprobación

| ID | Decisión |
|---|---|
| DBE-022 | Una baja normal exige que el activo esté Disponible, sin custodia vigente, y motivo obligatorio. Puede aplicarse a cualquier condición, incluido Operativo por obsolescencia. Conserva autor, fecha y toda la ficha/historial; no borra el activo. |
| DBE-023 | Dar de baja un activo No localizado requiere solicitud y aprobación independiente; un gestor no puede aprobar su propia solicitud. |
| DBE-024 | La aprobación de baja aplica solo a activos No localizados, no a bajas normales después de devolución/revisión. |
| DBE-025 | El revisor debe pertenecer a una facultad distinta de la responsable del activo y tener permiso técnico limitado: ver solicitudes asignadas y aprobar/rechazar, sin editar inventario. |
| DBE-026 | La solicitud guarda motivo, autor y fecha; la decisión guarda revisor y fecha. Rechazar exige motivo y mantiene el activo No localizado; aprobar registra la baja. |
| DBE-027 | Habrá una interfaz para el flujo de solicitudes/decisiones y otra para administrar cuentas revisoras. Un operador técnico autorizado mantiene las cuentas y la lista manual de facultades; no se crea un cargo institucional nuevo. |
| DBE-028 | Gestores mantienen iguales permisos ordinarios. Su alta/baja es por comandos locales, sin auto-registro público ni API de administración de gestores. |
| DBE-029 | Una baja válida es terminal. Si se registró por error, solo puede rectificarse como error más reciente, vinculando la rectificación y su motivo; nunca se elimina el original. |

## Licencias, QR e importación

| ID | Decisión |
|---|---|
| DBE-030 | El inventario de licencias es independiente de los activos físicos; un activo no necesita tener una licencia asociada. |
| DBE-031 | Se controlan licencias de puestos finitos por usuario o dispositivo. No se incluyen licencias ilimitadas/de campus ni asignación individual a una persona o equipo. |
| DBE-032 | Cada lote guarda software, proveedor, tipo, cantidad comprada, cantidad en uso y fechas de vigencia; disponibles se calcula como compradas menos en uso. Fecha de inicio obligatoria y fecha de fin opcional; edición auditada; no se guardan claves. |
| DBE-033 | Cada activo físico tiene QR descargable para imprimir. Codifica un enlace interno con el código TI y sin datos personales; al abrirlo exige autenticación y después muestra la ficha. |
| DBE-034 | CSV se ofrece tanto para activos físicos como para lotes de licencias, usando plantillas/reglas distintas. |
| DBE-035 | CSV valida todas las filas; si una falla, se rechaza el lote completo. La vista previa muestra errores antes de dos confirmaciones explícitas. |
| DBE-036 | Los códigos TI son generados por el servidor durante la importación; activos nuevos quedan Disponibles/sin custodio. Los lotes se importan en una transacción íntegra. |
| DBE-037 | El historial funcional se conserva sin borrado automático. El código de un activo dado de baja no se reutiliza. |

## Decisiones técnicas que se documentan en planes

Las alternativas técnicas de API, migraciones, tablas de auditoría, biblioteca de QR y protección transaccional se documentan en plan/research por incremento. No alteran las reglas funcionales anteriores. El plan debe conservar compatibilidad con el stack ya fijado en 002 y señalar explícitamente cualquier dependencia nueva.
## Aclaraciones posteriores

| ID | Decisión |
|---|---|
| DBE-038 | Al cerrar mantenimiento se exige registrar la ubicación de recepción. Se precarga la última ubicación previa al taller como valor editable; el gestor confirma explícitamente antes de guardar. |
| DBE-039 | El operador técnico crea revisores desde interfaz con contraseña temporal; el revisor debe cambiarla en su primer inicio. No hay autoregistro ni correo de invitación. |
| DBE-040 | Tras rechazo de baja No localizado, un Gestor puede presentar otra solicitud con motivo actualizado. |
| DBE-041 | La recuperación cancela automáticamente una solicitud de baja pendiente, registrando motivo/cause, fecha y vínculo al evento de recuperación. |
| DBE-042 | No se desactiva un revisor con solicitudes pendientes hasta reasignarlas a otro revisor elegible; se preserva autoría de asignaciones y decisiones. |
| DBE-043 | Para baja normal de un activo con mantenimiento En curso, primero se cierra el mantenimiento con resultado; luego se tramita la baja. |
| DBE-044 | Inicio de vigencia de lote de licencia siempre obligatorio; fin opcional. Si venció, se conserva y muestra el remanente calculado junto al estado Vencido. |
| DBE-045 | El QR contiene enlace interno que puede abrirse fuera de la app; se solicita login y, luego de autenticar como Gestor, se abre la ficha. |
| DBE-046 | La importación CSV también cubre lotes de licencias con plantilla distinta y el mismo flujo estricto: validar todo, rechazar lote inválido y aplicar lote válido con dos confirmaciones y atomicidad. |
| DBE-047 | La primera cuenta de operador técnico se provisiona mediante comando local; la gestión funcional de facultades/revisores se realiza en la interfaz autorizada. |
| DBE-048 | Los activos existentes de 002 deben recibir manualmente una facultad responsable con datos verificados antes de aplicar la migración que la exige. No se inventan asignaciones. |
| DBE-049 | El mismo Gestor que carga el CSV debe completar ambas confirmaciones; el lote aplicado es idempotente ante reintentos. |
| DBE-050 | Cambiar la facultad responsable de un activo es una operación exclusiva del operador técnico, con motivo e historial antes/después. No se permite mientras exista una solicitud de baja pendiente para el activo. |
| DBE-051 | La reasignación de solicitudes pendientes de un revisor desactivado la realiza exclusivamente el operador técnico; se conserva la autoría de la reasignación. |
