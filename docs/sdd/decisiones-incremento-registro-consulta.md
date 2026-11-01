# Decisiones del incremento de registro y consulta de activos

**Fecha:** 20 de octubre de 2026 (America/Guayaquil).
**Fuente:** respuestas explícitas de Steven en la conversación de preparación del incremento.
**Estado:** decisiones funcionales integradas; diseño, tareas, análisis e implementación completados y validados localmente. Evidencia en specs/002-registro-consulta-activos/validation.md; revisión humana pendiente.

## Decisiones confirmadas

| ID | Decisión | Evidencia |
|---|---|---|
| DEC-001 | Esta entrega incluirá API, pruebas y pantalla web. | Steven eligió «API, pruebas y pantalla web». |
| DEC-002 | Conservar la integración de Copilot y agregar la de Codex. | Steven eligió «Conservar Copilot y agregar Codex». |
| DEC-003 | Preguntar antes de incorporar funcionalidades o reglas no definidas. | Steven indicó «EVITA ASUMIR una funcionalidad, preferible pregunta». |
| DEC-004 | La pantalla incluirá listado de activos, ficha individual, búsqueda y filtros. Los criterios de búsqueda y los filtros concretos siguen por definir. | Steven eligió «Listado, ficha, búsqueda y filtros; definiremos cuáles». |
| DEC-005 | Conservar todos los datos propuestos: código único de inventario, nombre o descripción, categoría, marca, modelo, número de serie, ubicación, custodio y estado. La obligatoriedad y la separación de nombre y descripción están pendientes de definición. | Steven respondió «Conservemos todos» a la lista de campos propuesta. |
| DEC-006 | Nombre y descripción serán dos campos separados. | Steven eligió «Dos campos separados: nombre y descripción». |
| DEC-007 | Nombre, descripción, categoría, marca, modelo, número de serie, ubicación, custodio y estado serán obligatorios al registrar un activo. El código único no apareció en la lista de obligatoriedad y su forma de asignación se consultará antes de definirla. | Steven enumeró explícitamente esos nueve campos como obligatorios. |
| DEC-008 | El sistema generará automáticamente el código único de inventario. Su formato y las demás reglas de generación siguen pendientes de definición. | Steven eligió «El sistema lo genera automáticamente». |
| DEC-009 | Rechazar duplicados de la combinación marca + modelo + número de serie. | Steven aceptó la recomendación con «Si, hagámoslo como mencionas». |
| DEC-010 | El código automático será único en todo el sistema y estable durante la vida del activo. Su formato y reglas específicas de generación siguen pendientes. | Steven aceptó la recomendación que distinguía el código de inventario de la combinación de marca, modelo y serie. |
| DEC-011 | Incluir las categorías computadora de escritorio, portátil, monitor, impresora, equipo de red y periférico. | Steven confirmó la lista propuesta con «Si están bien esas». |
| DEC-012 | Separar condición (Operativo, Averiado, En reparación) y asignación (Disponible, Asignado). En reparación será una condición registrada, sin órdenes ni procesos de mantenimiento en este incremento. | Steven eligió «Sí, separar condición y asignación» ante esa propuesta explícita. |
| DEC-013 | Condición y asignación serán campos obligatorios. | Steven eligió «Sí, ambos serán obligatorios». |
| DEC-014 | Distinguir al gestor del inventario del custodio temporal del activo. Una devolución termina la custodia temporal actual y el activo permanece bajo el control del inventario. Esto revisa la interpretación inicial de custodio temporal siempre obligatorio de DEC-007. | Steven explicó el caso de entrega de una FPGA a un profesor y su devolución. |
| DEC-015 | Incluir entregas, devoluciones e historial básico en este incremento, junto con registro y consulta mediante API y pantalla web. | Steven eligió «Sí: incluir entregas, devoluciones e historial básico». |
| DEC-016 | Varios gestores autorizados pueden operar; conservar el gestor autor de cada movimiento. No se fija un gestor responsable único por activo. | Steven eligió «Varios gestores autorizados; registrar el autor de cada movimiento». |
| DEC-017 | Solo los gestores acceden a la aplicación. Los custodios se registran como personas sin cuenta de acceso en esta entrega. | Steven eligió «Solo los gestores acceden; el custodio se registra como persona». |
| DEC-018 | Alta inicial siempre Disponible y sin custodio temporal. La custodia se registra después mediante una entrega; no se permite alta inicial Asignada en este incremento. | Steven eligió «Siempre disponible y sin custodio; registrar después la entrega». |
| DEC-019 | Permitir entregar solo activos Disponibles y Operativos. La entrega inicia la custodia temporal y deja el activo Asignado. | Steven confirmó «Sí, solo activos disponibles y operativos», junto con la regla de asignación mediante entrega de DEC-018. |
| DEC-020 | La devolución exige indicar la condición recibida, deja Disponible y sin custodio temporal y conserva en el historial condiciones anterior y recibida. Una nueva entrega requiere que esté Operativo. | Steven confirmó «Sí, aplicar esa regla de devolución» ante la propuesta completa. |
| DEC-021 | Cada movimiento conserva activo, tipo de operación, fecha/hora de registro automáticas, gestor autor, custodio relacionado, condiciones anterior/posterior y observación opcional. | Steven eligió «Sí, guardar ese conjunto de datos» ante la lista completa. |
| DEC-022 | Conservar el movimiento original y añadir una rectificación vinculada con motivo obligatorio, autor y fecha; corregir también la situación actual si el error afecta custodia o condición. | Steven eligió «Conservar el original y añadir una rectificación con motivo obligatorio» ante la propuesta completa. |
| DEC-023 | Rectificar solo el último movimiento vigente del activo, sin rectificar operaciones anteriores que ya tengan movimientos posteriores. | Steven eligió «Sí, rectificar solo el último movimiento vigente del activo». |
| DEC-024 | La rectificación anula el efecto del último movimiento y restaura la situación anterior. La operación correcta se registra después como una nueva operación separada. | Steven eligió «Anular el efecto, restaurar la situación anterior y registrar la operación correcta después». |
| DEC-025 | Permitir Cambiar condición de activos Disponibles con motivo obligatorio e historial. Distinguir el cambio real de la rectificación de un error; no añadir órdenes ni gestión detallada de mantenimiento. | Steven eligió «Sí, permitir cambiar condición de activos Disponibles con motivo e historial», manteniendo la delimitación de mantenimiento de DEC-012. |
| DEC-026 | Custodio con nombre completo y correo institucional obligatorios, correo único y dependencia opcional, sin cuenta de acceso. | Steven eligió «Sí: nombre y correo obligatorios, correo único y dependencia opcional». |
| DEC-027 | Ubicación actual informada: registrar destino en entregas y lugar de recepción en devoluciones, actualizando la ficha. | Steven eligió «Ubicación actual informada; registrar destino en entregas y recepción en devoluciones». |
| DEC-028 | Búsqueda parcial sin distinguir mayúsculas en código, nombre del activo, marca, modelo, serie y nombre/correo del custodio actual; filtros por categoría, condición, asignación, ubicación y custodio; todos los criterios seleccionados deben cumplirse a la vez. | Steven eligió «Sí, usar esa búsqueda y esos filtros combinados» ante la propuesta completa. |
| DEC-029 | Código automático con prefijo TI- y numeración creciente como TI-000001 y TI-000002; sin reinicio por año/categoría ni reutilización de códigos. | Steven eligió «Sí, usar TI- y numeración automática creciente» ante la propuesta completa. |
| DEC-030 | Comparar marca, modelo, serie y correo sin distinguir mayúsculas y eliminando espacios exteriores; conservar los caracteres internos de la serie, distinguiendo ABC-123 de ABC123. | Steven eligió «Sí, aplicar esas reglas de comparación». |
| DEC-031 | Marca, modelo y ubicación se ingresan como texto; no administrar esos catálogos en este incremento. | Steven eligió «Texto para marca, modelo y ubicación; sin administrar esos catálogos en esta entrega». |
| DEC-032 | La FPGA fue solo un ejemplo; mantener las seis categorías aprobadas sin añadir otra ni clasificar ese ejemplo. | Steven respondió «Era un ejemplo, no incluamos nada aún». |
| DEC-033 | Todos los gestores autorizados tienen iguales permisos sobre todo el inventario, incluido registrar custodios y rectificar movimientos elegibles de otro gestor, conservando cada autor. | Steven eligió «Sí, mismos permisos para todos los gestores sobre el inventario completo». |
| DEC-034 | Rechazar devolución sin entrega activa, rectificación duplicada, rectificación de rectificación y habilitar operaciones antiguas tras anular la última. Solo rectificar la última entrega, devolución o cambio de condición vigente sin operaciones posteriores. | Steven eligió «Sí, aplicar esas restricciones» ante la propuesta completa. |
| DEC-035 | Validar formato de correo de custodio sin restringir dominio por ahora. | Steven eligió «Validar formato de correo, sin restringir dominio por ahora». |
| DEC-036 | Conservar todo el historial sin borrado automático en la entrega académica; definir los plazos institucionales en una etapa posterior. | Steven eligió «Sí, conservar historial y definir plazos institucionales después». |

Estas decisiones expresan el alcance indicado por Steven para el trabajo académico. La ratificación grupal de la constitución y las políticas institucionales conservan su estado pendiente.

## Preparación de herramientas realizada

Se agregó Codex mediante `specify integration install codex --force`, manteniendo Copilot. Copilot continúa como integración predeterminada; Codex cuenta con diez skills en `.agents/skills/` y configuración de scripts PowerShell.

`specify integration status` informa `unsafe-multi-install` porque Copilot no declara coexistencia automática segura. La instalación múltiple fue elegida explícitamente por Steven. También informa 22 archivos administrados modificados: se comprobó que sus diferencias con los hashes de manifiesto se limitan a saltos de línea CRLF/LF y que su contenido no cambió respecto a HEAD. Los diez archivos nuevos de Codex coinciden con los hashes de su manifiesto. No se actualizaron forzosamente las plantillas ni los scripts compartidos.

## Estado de las decisiones y trabajo siguiente

Las dudas funcionales identificadas se cerraron con las respuestas registradas. DEC-004–DEC-010 reflejan la secuencia histórica: sus pendientes iniciales se resolvieron mediante decisiones posteriores. DEC-014 y DEC-018 sustituyen la interpretación inicial de custodio obligatorio al alta; el alta es Disponible sin custodio y una entrega inicia la custodia.

La conservación institucional a largo plazo se difiere expresamente (DEC-036). La constitución sigue como propuesta sin ratificación. Se elaboraron plan, investigación, modelo de datos, contratos y guía de validación en specs/002-registro-consulta-activos/. Se generaron 38 tareas y se ejecutaron análisis e implementación; cualquier nueva duda funcional se consultará antes de adoptarse. La implementación se acredita con pruebas y comprobación de navegador, no por estar escrita en la especificación.
