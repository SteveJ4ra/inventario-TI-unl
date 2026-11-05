# Especificación de funcionalidad: registro, consulta y custodia de activos físicos

**Rama de trabajo:** `feature/registro-consulta-activos`
**Identificador:** `002-registro-consulta-activos`
**Creado:** 20 de octubre de 2026
**Estado:** incremento implementado y validado localmente; resultados en [validation.md](validation.md). Revisión humana del equipo pendiente.
**Entrada:** Desarrollar registro, consulta, entregas, devoluciones, cambios de condición de activos disponibles, rectificaciones e historial de activos físicos mediante API y pantalla web, con pruebas; listado, ficha individual, búsqueda y filtros. Distinguir gestores autorizados y custodios temporales. Aplicar únicamente las decisiones confirmadas por Steven y consultar las reglas restantes antes de adoptarlas.
**Fuentes:** [Registro de decisiones](../../docs/sdd/decisiones-incremento-registro-consulta.md) y [especificación inicial de contexto](../001-inventario-ti/spec.md).

## Clarifications

### Session 2026-10-20

- Q: Al separar estado en condición y asignación, ¿ambos campos serán obligatorios? → A: Sí, ambos serán obligatorios.
- Q: ¿Qué representa el custodio cuando un activo está disponible? → A: Se distinguen el gestor que controla y registra las operaciones del inventario y el custodio temporal que tiene el activo, por ejemplo un profesor. Tras la devolución termina la custodia temporal y se conserva el control del inventario. Esta distinción sustituye la interpretación de custodio temporal siempre obligatorio.
- Q: ¿Este incremento incluirá entregas, devoluciones e historial básico? → A: Sí; se incorporan al alcance junto con registro y consulta.
- Q: ¿Cada activo tendrá un gestor responsable fijo o podrá gestionarlo cualquier gestor autorizado? → A: Varios gestores autorizados pueden operar y se conserva el autor de cada movimiento; no se establece un gestor fijo por activo.
- Q: ¿Los custodios tendrán cuenta para acceder a la aplicación en esta entrega? → A: Solo los gestores acceden; el custodio se registra como persona y no tendrá cuenta de acceso en este incremento.
- Q: ¿Cómo se registra la asignación y custodia inicial de un activo? → A: Siempre Disponible y sin custodio temporal; la entrega se registra después.
- Q: ¿Cuándo se permite entregar un activo? → A: Solo si está Disponible y Operativo.
- Q: ¿Qué debe ocurrir al registrar una devolución? → A: El gestor indica la condición recibida; el activo queda Disponible y sin custodio temporal. El historial conserva la condición anterior y la recibida; solo puede volver a entregarse si está Operativo.
- Q: ¿Qué datos conservará el historial básico en cada movimiento? → A: Activo, tipo de operación, fecha y hora de registro automáticas, gestor autor, custodio relacionado, condición anterior y posterior y una observación opcional del gestor.
- Q: ¿Cómo se corrige una entrega o devolución registrada por error? → A: Conservar el movimiento original y añadir una rectificación vinculada con motivo obligatorio, autor y fecha; corregir también la situación actual si el error afecta custodia o condición.
- Q: ¿Qué movimientos pueden rectificarse en este incremento? → A: Solo el último movimiento vigente de cada activo; no se modifican operaciones anteriores que ya tengan movimientos posteriores.
- Q: ¿Qué efecto tiene la rectificación del último movimiento? → A: Anular su efecto y restaurar la situación anterior, conservando el original y la rectificación. Después se registra por separado la operación correcta.
- Q: ¿Cómo se registra un cambio real de condición, por ejemplo una reparación? → A: Se permite Cambiar condición para activos Disponibles, con motivo obligatorio e historial; no se trata como rectificación de un error anterior.
- Q: ¿Qué datos identificarán a cada custodio? → A: Nombre completo y correo institucional obligatorios, correo único y dependencia opcional; la persona no tiene cuenta de acceso.
- Q: ¿Qué representa la ubicación del activo? → A: La ubicación actual informada; registrar el destino al entregarlo y el lugar de recepción al devolverlo, actualizando la ficha.
- Q: ¿Qué búsqueda y filtros tendrá el listado? → A: Búsqueda parcial sin distinguir mayúsculas en código, nombre del activo, marca, modelo, serie y nombre/correo del custodio actual; filtros por categoría, condición, asignación, ubicación y custodio. Deben cumplirse conjuntamente la búsqueda y todos los filtros seleccionados.
- Q: ¿Qué formato tendrá el código automático? → A: Prefijo TI- y numeración automática creciente, como TI-000001 y TI-000002; no reiniciar por año ni categoría y no reutilizar códigos.
- Q: ¿Cómo se comparan marca, modelo, serie y correo para detectar duplicados? → A: Ignorar mayúsculas y espacios exteriores, conservando los caracteres internos de la serie. DELL equivale a « dell » y ABC-123 a « abc-123 », pero ABC-123 no equivale a ABC123.
- Q: ¿Marca, modelo y ubicación requieren catálogos administrables? → A: Se ingresan como texto en esta entrega; no se incorpora la administración de esos catálogos.
- Q: ¿Añadimos una categoría para la FPGA del ejemplo? → A: No; era únicamente un ejemplo. Se mantienen las seis categorías aprobadas, sin añadir Placas de desarrollo ni asignar una clasificación a ese ejemplo.
- Q: ¿Qué permisos tendrán los gestores? → A: Todos los gestores autorizados tienen los mismos permisos sobre el inventario completo: registrar activos y custodios, consultar, entregar, devolver, cambiar condición y rectificar el último movimiento elegible, aunque lo registrara otro gestor.
- Q: ¿Qué devoluciones y rectificaciones se rechazan? → A: Devolución sin entrega activa; rectificar dos veces el mismo movimiento; rectificar una rectificación; y volver elegible un movimiento antiguo después de anular el último. Solo es rectificable la última entrega, devolución o cambio de condición vigente, sin operaciones posteriores.
- Q: ¿Restringimos el correo del custodio a @unl.edu.ec? → A: Validar el formato de correo sin restringir el dominio por ahora; conservar nombre y correo obligatorios y correo único según la comparación acordada.
- Q: ¿Cómo conservamos el historial en esta entrega? → A: Conservar todo el historial sin borrado automático; definir los plazos institucionales de conservación en una etapa posterior.

## Clarificación posterior sobre filtros

Tras la observación docente sobre la cantidad de controles, la búsqueda visual presenta tres filtros: categoría, situación y condición, junto con la búsqueda general existente. La situación incluye Disponible, Asignado, No localizado y Baja. Disponible exige activo localizado, asignación disponible y ausencia de mantenimiento en curso. Asignado exige activo localizado y asignación asignada. No localizado y Baja corresponden al ciclo de vida. La condición física se mantiene independiente.

El parámetro HTTP adicional situation aplica estos criterios y se combina con los demás filtros. Los parámetros previos assignment, location y custodian siguen admitiéndose para clientes existentes. Una situación inválida se rechaza con HTTP 400. Esta clarificación actualiza la presentación de FR-009 sin alterar la definición histórica de DEC-028.

## Escenarios de usuario y comprobación

El orden presenta primero el registro, después las entregas y devoluciones y finalmente las consultas. La gestión puede ser realizada por distintos gestores autorizados; cada movimiento conserva su autor. Solo los gestores acceden a la aplicación en este incremento; los custodios se registran como personas sin cuenta. Todos los gestores autorizados tienen los mismos permisos sobre el inventario completo, incluidos los movimientos registrados por otros gestores.

### Historia 1 - Registrar un activo identificado individualmente (P1)

Como gestor autorizado, quiero guardar los datos de un equipo físico y recibir su código de inventario para distinguirlo de los demás equipos.

**Razón del orden:** el registro incorpora la información que se consultará después.
**Comprobación independiente:** registrar un equipo ficticio con los datos requeridos y comprobar su ficha e identidad generada, usando un gestor autorizado y las seis categorías confirmadas.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dado** un registro con los datos obligatorios completos y válidos, **cuando** se guarda correctamente, **entonces** el sistema genera un código único de inventario asociado al nuevo activo, con asignación Disponible y sin custodio temporal.
2. **Dado** un activo registrado, **cuando** se intenta registrar otro con la misma combinación de marca, modelo y número de serie, **entonces** se rechaza el duplicado. Se comparan marca, modelo y serie sin distinguir mayúsculas y eliminando espacios exteriores; se conservan los caracteres internos de la serie.
3. **Dado** un formulario sin uno de los datos obligatorios confirmados, **cuando** se intenta registrar el activo, **entonces** el registro se rechaza.
4. **Dados** nombre, descripción y los demás campos requeridos, **cuando** se registra y consulta el activo, **entonces** se conservan por separado, con una de las seis categorías y una condición admitida; marca, modelo y ubicación se ingresan como texto.
5. **Dado** un custodio nuevo, **cuando** un gestor registra nombre completo y correo de formato válido, con dependencia opcional, **entonces** puede seleccionarlo en una entrega; no recibe cuenta de acceso y el dominio del correo no limita el registro.
6. **Dado** un correo ya registrado, **cuando** se intenta registrar otro custodio con un correo equivalente por mayúsculas o espacios exteriores, **entonces** se rechaza; también se rechazan nombre o correo vacíos y correos con formato inválido.
7. **Dados** distintos activos válidos registrados sucesivamente, **cuando** reciben sus códigos, **entonces** estos usan TI- y numeración creciente con al menos seis dígitos, sin reinicio por categoría o año ni reutilización de códigos previos.

### Historia 2 - Registrar una entrega y una devolución (P1)

Como gestor autorizado, quiero registrar la entrega de un activo a un custodio temporal y su posterior devolución para conocer quién lo tiene y conservar la trazabilidad de las operaciones.

**Razón del orden:** representa el recorrido descrito por Steven y diferencia el control del inventario de la custodia temporal.
**Comprobación independiente:** usar un activo ficticio registrado, una persona receptora y gestores autorizados; comprobar entrega, devolución e historial de acuerdo con las reglas siguientes.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dado** un activo Disponible y Operativo, **cuando** un gestor registra la entrega a una persona e indica la ubicación de destino, **entonces** queda Asignado, se identifica al custodio temporal, se actualiza la ubicación actual informada y se conservan destino y autor del movimiento.
2. **Dado** un activo con custodia temporal activa, **cuando** un gestor registra su devolución e indica la condición recibida y el lugar de recepción, **entonces** queda Disponible y sin custodio temporal, se actualiza su ubicación actual informada y se conservan el movimiento, autor, lugar de recepción, condiciones anterior/recibida y antecedente de entrega.
3. **Dadas** una entrega y una devolución del mismo activo, **cuando** un gestor autorizado consulta el historial básico, **entonces** puede distinguir las dos operaciones, sus autores y quién tuvo la custodia temporal.

4. **Dado** un activo Asignado o cuya condición es Averiado o En reparación, **cuando** se intenta realizar una entrega, **entonces** se rechaza la operación.
5. **Dado** un activo devuelto como Averiado o En reparación, **cuando** se intenta entregarlo otra vez, **entonces** se rechaza aunque su asignación sea Disponible.

6. **Dado** un activo sin entrega activa, **cuando** se intenta registrar una devolución, **entonces** se rechaza sin alterar la ficha ni crear un movimiento válido. La ubicación representa el lugar actual informado y se actualiza con el destino de la entrega y la recepción de la devolución.

---

### Historia 3 - Rectificar un movimiento sin perder su antecedente (P2)

Como gestor autorizado, quiero corregir un error del último movimiento vigente mediante una rectificación vinculada para conservar la trazabilidad del original y mantener coherente la situación actual del activo.

**Razón del orden:** permite tratar errores de registro sin reescribir entregas o devoluciones originales.
**Comprobación independiente:** disponer de un activo con movimientos ficticios y comprobar el vínculo de rectificación, su motivo y el rechazo de un movimiento que ya tenga operaciones posteriores. La rectificación anula el efecto del movimiento y restaura la situación anterior; la operación correcta se registra después por separado.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dado** el último movimiento vigente de un activo, **cuando** un gestor registra una rectificación válida con motivo, **entonces** el original se conserva y queda vinculada la rectificación con su autor y fecha.
2. **Dado** un movimiento con operaciones posteriores, **cuando** se intenta rectificarlo, **entonces** se rechaza la rectificación.
3. **Dada** una solicitud de rectificación sin motivo, **cuando** se intenta registrarla, **entonces** se rechaza.
4. **Dado** un error en el último movimiento rectificable, **cuando** se registra su rectificación válida, **entonces** se anula su efecto y se restaura la situación anterior a ese movimiento, conservando el original y la rectificación.
5. **Dada** una rectificación completada, **cuando** el gestor necesita dejar registrada la operación correcta, **entonces** la registra como una operación nueva y separada que cumple las reglas correspondientes.
6. **Dado** un movimiento ya rectificado o que es una rectificación, **cuando** se intenta rectificarlo, **entonces** se rechaza.
7. **Dadas** una entrega A, una devolución B y una rectificación de B, **cuando** se intenta rectificar A, **entonces** se rechaza: anular B no elimina la existencia de operaciones posteriores a A.
8. **Dado** un movimiento elegible registrado por otro gestor, **cuando** un gestor autorizado lo rectifica con motivo, **entonces** la rectificación conserva su propio autor y el original conserva el suyo; se restauran condición, asignación, custodio y ubicación anteriores.

---

### Historia 4 - Registrar un cambio real de condición (P2)

Como gestor autorizado, quiero cambiar la condición de un activo Disponible con un motivo para reflejar su situación real sin confundir una reparación o avería con un error de registro.

**Razón del orden:** permite que un equipo Disponible pase, por ejemplo, de Averiado a En reparación y después a Operativo, conservando los antecedentes.
**Comprobación independiente:** disponer de un activo Disponible, registrar un cambio de condición con motivo y contrastar la condición actual con el historial.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dado** un activo Disponible, **cuando** un gestor registra un cambio a otra condición admitida con motivo, **entonces** se actualiza la condición y se conserva el cambio, motivo, autor, fecha/hora y condiciones anterior/posterior en el historial.
2. **Dado** un activo Asignado, **cuando** se intenta usar Cambiar condición, **entonces** se rechaza esa operación en este incremento.
3. **Dada** una solicitud de cambio de condición sin motivo, **cuando** se intenta guardarla, **entonces** se rechaza.
4. **Dado** un equipo Disponible que vuelve a Operativo mediante un cambio válido, **cuando** se solicita su entrega, **entonces** cumple las condiciones de disponibilidad y condición necesarias para entregarlo.

---

### Historia 5 - Consultar el listado y la ficha individual (P2)

Como gestor autorizado, quiero ver los activos registrados y abrir su ficha individual para conocer la información de un equipo específico.

**Razón del orden:** permite comprobar y utilizar la información registrada.
**Comprobación independiente:** disponer de activos ficticios previamente registrados, consultar el listado y abrir la ficha de cada uno.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dados** dos activos diferentes, **cuando** se abren sus fichas, **entonces** cada ficha presenta su propio código y los datos del activo correspondiente.
2. **Dado** un activo registrado, **cuando** se consulta repetidamente su ficha, **entonces** el código de inventario permanece estable.
3. **Dada** una persona sin sesión o sin autorización de gestor, **cuando** intenta consultar o modificar inventario, custodios o historial, **entonces** se deniega el acceso.
4. **Dados** dos gestores autorizados, **cuando** consultan o realizan las mismas operaciones válidas sobre cualquier activo, **entonces** ambos tienen los mismos permisos, conservando al autor real de cada operación.
5. **Dado** un inventario vacío o una búsqueda sin coincidencias, **cuando** se consulta el listado, **entonces** se presenta el estado sin resultados; una ficha inexistente se informa como inexistente sin presentar datos de otro activo.
6. **Dado** el historial de un activo, **cuando** se consulta después de devoluciones y rectificaciones, **entonces** se conservan todos sus registros, originales y rectificaciones; este incremento no ejecuta borrado automático.

### Historia 6 - Encontrar activos mediante búsqueda y filtros (P3)

Como gestor autorizado, quiero buscar y filtrar el listado para localizar los equipos que necesito revisar.

**Razón del orden:** facilita localizar información dentro del conjunto registrado.
**Comprobación independiente:** preparar activos de distintas categorías, condiciones, asignaciones, ubicaciones y custodios, y contrastar las fichas devueltas por la búsqueda parcial y los filtros combinados.

**Escenarios de aceptación derivados de decisiones confirmadas:**

1. **Dado** un activo cuyo código, nombre, marca, modelo, serie o nombre/correo de custodio actual contiene un fragmento buscado, **cuando** se busca ese fragmento sin distinguir mayúsculas, **entonces** el activo satisface el criterio de búsqueda.
2. **Dados** activos que pertenecen a distintas categorías y asignaciones, **cuando** se filtra por Portátil y Disponible, **entonces** solo se muestran los que cumplen ambos criterios.
3. **Dados** una búsqueda y filtros de categoría, condición, asignación, ubicación o custodio, **cuando** se combinan, **entonces** cada resultado satisface la búsqueda y todos los filtros seleccionados.
4. **Dado** que ningún activo cumple los criterios combinados, **cuando** se consulta el listado con esos criterios, **entonces** no se presentan activos que incumplan alguno de ellos.

### Casos límite y respuestas esperadas

- Rechazar combinaciones de marca, modelo y serie equivalentes por mayúsculas o espacios exteriores. Conservar la distinción entre series ABC-123 y ABC123.
- Rechazar un correo de custodio repetido aunque difiera en mayúsculas o espacios exteriores.
- Dos altas simultáneas del mismo equipo: aceptar como máximo una ficha para la combinación normalizada de marca, modelo y serie.
- Altas simultáneas de activos distintos: generar códigos diferentes sin reinicio ni reutilización.
- Ficha inexistente: informar que no existe; listado vacío o búsqueda sin coincidencias: mostrar estado sin resultados.
- Activo sin custodia temporal actual después de una devolución: conservar los antecedentes y el autor de cada movimiento.
- Rechazar entregas de activos ya Asignados o no Operativos.
- Rechazar devoluciones sin entrega activa, sin cambiar la ficha ni registrar una devolución válida.
- Operaciones simultáneas sobre el mismo activo: cada operación aceptada cumple las reglas sobre el estado vigente; no permitir doble entrega ni doble devolución o rectificación del mismo movimiento.
- Rectificación de un movimiento con operaciones posteriores, rectificación sin motivo y dos rectificaciones simultáneas sobre el mismo último movimiento.
- Rechazar una segunda rectificación del mismo movimiento y cualquier rectificación de una rectificación. Anular el último movimiento no vuelve elegibles los anteriores.
- Cambio de condición sin motivo o sobre un activo Asignado: rechazar.
- Distinguir la rectificación de un error de un cambio real de condición.
- Disponible significa sin asignación actual: un activo Disponible pero Averiado o En reparación no puede entregarse. Los cambios reales de condición se registran para activos Disponibles con motivo e historial.

## Requisitos

### Requisitos funcionales

- **FR-001:** permitir registrar y consultar activos físicos, registrar entregas y devoluciones, rectificar movimientos, cambiar la condición de activos Disponibles y consultar su historial mediante pantalla web y API. La entrega incluirá pruebas de las funcionalidades acordadas.
- **FR-002:** generar automáticamente un código de inventario único y estable con prefijo `TI-` y numeración creciente, presentada como `TI-000001`, `TI-000002`, etc. La numeración no se reinicia por año ni categoría y no se reutilizan códigos.
- **FR-003:** conservar nombre y descripción como campos separados, además de categoría, marca, modelo, número de serie, ubicación y custodio.
- **FR-004:** exigir nombre, descripción, categoría, marca, modelo, número de serie y ubicación al registrar el activo. El custodio representa a la persona que tiene la custodia temporal; no se exige ni se asigna custodio temporal al dar de alta el activo o después de una devolución.
- **FR-005:** exigir los dos campos separados: condición (`Operativo`, `Averiado` o `En reparación`) y asignación (`Disponible` o `Asignado`). Al dar de alta se establece Disponible; esto no implica que su condición sea Operativo.
- **FR-006:** utilizar las categorías confirmadas: computadora de escritorio, portátil, monitor, impresora, equipo de red y periférico.
- **FR-007:** rechazar un activo duplicado por la combinación marca + modelo + serie, comparando los tres campos sin distinguir mayúsculas y eliminando espacios al principio y al final. Conservar los caracteres internos de la serie: ABC-123 y ABC123 son distintos. La serie por sí sola no se establece como identificador único global.
- **FR-008:** permitir ver el listado de activos y la ficha individual de cada equipo registrado.
- **FR-009:** permitir buscar por coincidencia parcial sin distinguir mayúsculas en al menos uno de estos campos: código, nombre del activo, marca, modelo, serie y nombre/correo del custodio actual. Permitir filtrar por categoría, condición, asignación, ubicación y custodio actual; cada resultado debe satisfacer la búsqueda y todos los filtros seleccionados.
- **FR-010:** restringir el acceso a la aplicación y sus operaciones a gestores identificados y autorizados. Los custodios se registran como personas sin cuenta de acceso en este incremento. Todos los gestores autorizados tienen los mismos permisos sobre el inventario completo: registrar activos y custodios, consultar, entregar, devolver, cambiar condición y rectificar movimientos elegibles, incluso si los registró otro gestor.
- **FR-011:** distinguir al gestor que registra operaciones del custodio temporal del activo. Distintos gestores autorizados pueden gestionar los activos; no se fija un gestor responsable único por activo.
- **FR-012:** permitir una entrega únicamente si el activo está Disponible y Operativo; la entrega lo deja Asignado a un custodio temporal identificado y conserva el gestor autor del movimiento.
- **FR-013:** rechazar devoluciones sin entrega activa. Al registrar una devolución válida, exigir que el gestor indique la condición de recepción entre Operativo, Averiado y En reparación; dejar el activo Disponible y sin custodio temporal; conservar el antecedente, el autor y las condiciones anterior y recibida en el historial.
- **FR-014:** conservar y consultar en cada movimiento el activo, tipo de operación, fecha y hora de registro generadas automáticamente, gestor autor, custodio relacionado y condiciones anterior y posterior, además de una observación opcional escrita por el gestor. El autor corresponde al gestor que realiza la operación; no es una persona elegida para sustituir a quien la registra.
- **FR-015:** dar de alta todos los activos como Disponible y sin custodio temporal. Cualquier custodia temporal posterior se inicia mediante una entrega registrada; no se permite un alta directamente Asignada en este incremento.
- **FR-016:** conservar sin reescritura ni borrado el movimiento original cuando se corrija un error; añadir una rectificación vinculada con motivo obligatorio, gestor autor y fecha/hora que anule su efecto y restaure la situación anterior. La operación correcta se registra después como una nueva operación separada; la rectificación no edita directamente los datos originales.
- **FR-017:** permitir rectificar únicamente la última entrega, devolución o cambio de condición vigente de cada activo, sin operaciones posteriores. Rechazar movimientos con operaciones posteriores, ya rectificados y las propias rectificaciones. Anular el último movimiento no habilita la rectificación de movimientos anteriores.
- **FR-018:** permitir Cambiar condición únicamente sobre activos Disponibles, eligiendo otra de las condiciones admitidas y exigiendo motivo. Conservar el cambio, su autor, fecha/hora y condiciones anterior/posterior en el historial. Esta operación representa un cambio real y no sustituye la rectificación de un registro erróneo.
- **FR-019:** identificar a cada custodio con nombre completo y correo institucional obligatorios y dependencia opcional. El correo es único entre custodios comparándolo sin distinguir mayúsculas y eliminando espacios exteriores; la persona no recibe una cuenta de acceso. Validar el formato del correo sin restringir el dominio en este incremento.
- **FR-020:** conservar la ubicación actual informada del activo; exigir y registrar la ubicación de destino en la entrega y el lugar de recepción en la devolución, actualizando la ficha y conservando esos lugares en los movimientos correspondientes. La rectificación restaura también la ubicación anterior si el movimiento anulado la cambió.
- **FR-021:** permitir introducir marca, modelo y ubicación como texto; no incorporar catálogos administrables para esos tres datos en este incremento. Se mantienen las categorías y los valores de condición/asignación ya confirmados.
- **FR-022:** conservar todo el historial de este incremento sin borrado automático. Los plazos institucionales de conservación se definirán en una etapa posterior, sin inventar una política institucional en este trabajo.
- **FR-023:** mantener las reglas de identidad y estado también ante solicitudes simultáneas: no crear duplicados, repetir códigos ni aceptar doble entrega, devolución o rectificación incompatible. Una operación rechazada no deja cambios parciales ni un movimiento válido.

### Datos y reglas confirmadas

| Tema | Situación actual |
|---|---|
| Obligatoriedad | Condición y asignación son obligatorias. El alta siempre es Disponible y sin custodio temporal; la entrega identifica al custodio y la devolución termina su custodia actual. |
| Comparación de duplicados | Marca + modelo + serie se comparan sin distinguir mayúsculas y sin espacios exteriores; se mantienen los caracteres internos de la serie. El correo del custodio usa la misma comparación de mayúsculas/espacios exteriores para su unicidad. |
| Código generado | Automático, único y estable; prefijo TI- y numeración creciente como TI-000001, sin reinicio por año/categoría ni reutilización. |
| Catálogos | Marca, modelo y ubicación son texto, sin administrar esos catálogos en este incremento. Custodios tienen datos confirmados; categorías y valores de condición/asignación están confirmados. La FPGA fue un ejemplo y no añade categorías. Todos los gestores pueden registrar personas custodias. |
| Consulta | Confirmada búsqueda parcial sin distinguir mayúsculas en código, nombre, marca, modelo, serie y nombre/correo del custodio actual; filtros por categoría, condición, asignación, ubicación y custodio, combinados con cumplimiento de todos los criterios. |
| Acceso y auditoría | Solo los gestores acceden; los custodios son personas sin cuenta. Datos básicos del historial confirmados, con fecha/hora automáticas y autor real. La corrección conserva el original y añade rectificación vinculada con motivo obligatorio, limitada al último movimiento vigente. La rectificación anula el efecto y restaura la situación anterior; todos los gestores comparten permisos; no se rectifican rectificaciones ni se habilitan movimientos antiguos. Se conserva todo el historial sin borrado automático; los plazos institucionales quedan para una etapa posterior. |
| Entregas y devoluciones | Entregar solo Disponible y Operativo; después queda Asignado a la persona receptora. Devolver exige condición recibida, deja Disponible y sin custodio temporal y conserva condiciones anterior/recibida. La ubicación actual informada se actualiza con destino y recepción; se rechaza una devolución sin entrega activa. |

### Entidades principales

- **Activo físico:** unidad tecnológica individual con código generado, nombre, descripción, categoría, marca, modelo, serie, ubicación, custodio, condición y asignación.
- **Categoría:** clasificación elegida entre las seis categorías confirmadas.
- **Ubicación:** lugar actual informado del activo. Se registra al darlo de alta, cambia al destino indicado en una entrega y al lugar de recepción indicado en una devolución. Se captura como texto, sin catálogo administrable en este incremento.
- **Gestor de inventario:** persona autorizada que registra operaciones. Se conserva el gestor autor de cada movimiento y puede intervenir más de un gestor sobre un mismo activo; no se define un gestor fijo por activo.
- **Custodio temporal:** persona que tiene el activo tras una entrega; su custodia actual termina con la devolución. Se distingue del gestor. Se registra como persona sin cuenta de acceso, con nombre completo y correo institucional obligatorios, correo único y dependencia opcional.
- **Movimiento de inventario:** entrega, devolución o cambio de condición relacionado con un activo y gestor autor; incluye fecha/hora de registro automáticas, condiciones anterior/posterior y observación opcional. Conserva al custodio relacionado cuando corresponde; un cambio de condición de un activo Disponible no crea custodia temporal.
- **Rectificación:** registro vinculado al último movimiento vigente que conserva el original, su motivo obligatorio, autor y fecha/hora. Anula el efecto del movimiento y restaura la situación anterior. La operación correcta, si corresponde, se registra por separado.

Estos conceptos no definen todavía tablas, relaciones técnicas ni catálogos administrables.

## Criterios de éxito

### Resultados comprobables derivados del alcance confirmado

- **SC-001:** un activo registrado correctamente tiene un código generado que lo diferencia de todos los demás y se mantiene al consultar su ficha.
- **SC-002:** dos intentos con combinaciones de marca, modelo y serie equivalentes por mayúsculas o espacios exteriores no producen dos activos. Los caracteres internos de la serie se conservan para distinguir, por ejemplo, ABC-123 de ABC123.
- **SC-003:** dos equipos del mismo modelo con series diferentes pueden conservar fichas individuales distintas, si cumplen las demás reglas de registro.
- **SC-004:** un registro que omite un campo obligatorio confirmado no se acepta.
- **SC-005:** para un conjunto conocido de activos, la búsqueda parcial sin distinguir mayúsculas y los filtros combinados presentan únicamente los activos que cumplen la búsqueda y todos los filtros seleccionados; cada ficha corresponde al activo elegido.
- **SC-006:** después de una entrega y una devolución válidas se puede consultar que ya no existe esa custodia temporal actual y reconstruir ambas operaciones, la persona que tuvo el activo y los gestores que las registraron, sin perder los antecedentes.
- **SC-007:** un activo recién registrado queda Disponible y sin custodio temporal; una entrega solo se acepta si también está Operativo; una devolución permite distinguir su condición anterior de la recibida y no habilita una nueva entrega mientras su condición no sea Operativo.
- **SC-008:** cada movimiento permite conocer el activo, operación, fecha/hora de registro, gestor autor, custodio relacionado y condiciones anterior/posterior; una observación vacía no impide registrar una operación válida.
- **SC-009:** toda corrección aceptada conserva el movimiento original y su rectificación vinculada con motivo, autor y fecha; no se acepta una rectificación sin motivo o dirigida a un movimiento anterior con operaciones posteriores. La rectificación restaura la situación anterior y se distingue de una operación correcta registrada posteriormente.
- **SC-010:** un cambio real de condición sobre un activo Disponible exige motivo y permite reconstruir condición anterior, nueva, autor y fecha/hora en el historial; no se acepta si el activo está Asignado.
- **SC-011:** un custodio registrado conserva nombre y correo institucional, permite omitir la dependencia y no admite duplicar un correo aunque cambien mayúsculas o espacios exteriores.
- **SC-012:** después de una entrega y una devolución válidas, la ubicación actual informada coincide respectivamente con el destino y la recepción registrados; sus movimientos conservan dichos lugares.
- **SC-013:** una persona sin acceso de gestor no puede leer ni modificar activos, custodios o historial; dos gestores autorizados pueden operar sobre todo el inventario con iguales permisos, registrando cada cual su propia autoría.
- **SC-014:** rechazar devolución sin entrega activa, rectificación duplicada, rectificación de rectificación y rectificación de un movimiento antiguo después de anular el último, sin alterar ficha ni historial válido.
- **SC-015:** al competir solicitudes simultáneas, no aparecen activos duplicados, códigos repetidos ni movimientos incompatibles; la ficha y el historial coinciden con las operaciones aceptadas.
- **SC-016:** todo el historial sigue consultable, incluidas operaciones rectificadas y sus rectificaciones, sin borrado automático en esta entrega.

Estos criterios definen el comportamiento esperado; no afirman que existan pruebas ejecutadas. Todavía no se acordaron objetivos de tiempo, volumen o disponibilidad, y no se asignan valores por defecto.

## Supuestos y dependencias

Se aplica la instrucción de Steven de consultar las dudas funcionales antes de adoptar reglas. Las respuestas confirmadas se han incorporado; las decisiones técnicas se resolverán en el plan y cualquier duda funcional nueva se consultará antes de incorporarla.

- El registro de decisiones distingue los acuerdos de esta conversación de políticas institucionales todavía no verificadas.
- La constitución existente continúa como propuesta pendiente de ratificación grupal; este borrador no cambia su estado.
- Los artefactos de `001-inventario-ti` se conservan como contexto inicial. Se incorporaron entregas, devoluciones e historial básico por decisión explícita de Steven; los demás movimientos del contexto inicial siguen sin incorporarse automáticamente.
- `En reparación` describe la condición del equipo. Se confirmó posteriormente una acción para registrar cambios reales de condición de activos Disponibles, con motivo e historial; no se incorporan órdenes de reparación ni gestión detallada de mantenimiento.
- Las decisiones técnicas se concretarán en el plan posterior, manteniendo el stack acordado por el grupo.
- Edición general, eliminación, traslados, aprobaciones y un historial completo de todo el ciclo de vida no tienen requisitos aprobados en este borrador. Las entregas y devoluciones, el cambio real de condición de activos Disponibles y la rectificación vinculada del último movimiento vigente sí forman parte del alcance confirmado.

### Estado de aclaraciones y límites

No quedan dudas funcionales críticas identificadas para este incremento. No se incorpora una categoría para el ejemplo de FPGA. Los plazos institucionales de conservación y las metas de producción (volumen, rendimiento, disponibilidad) quedan fuera de la validación académica actual; no se atribuyen políticas institucionales no verificadas. La ratificación de la constitución por el grupo sigue pendiente y no se declara realizada.

La cobertura de aceptación se comprobará en API y pantalla web con datos ficticios. Esta tabla vincula los requisitos al recorrido y al resultado comprobable; todavía no representa pruebas ejecutadas.

| Requisitos | Aceptación y resultado |
|---|---|
| FR-001 | Historias 1–6 y SC-001–SC-016: recorridos por API y web, con pruebas de las reglas. |
| FR-002 | Historia 1.7, Historia 5.2, SC-001 y SC-015: código generado, estable y sin colisiones. |
| FR-003–FR-006, FR-015, FR-021 | Historia 1.1, 1.3–1.4 y SC-004/SC-007: campos separados, obligatorios, valores admitidos y alta Disponible sin custodio. |
| FR-007 | Historia 1.2 y SC-002/SC-003/SC-015: unicidad compuesta normalizada, equipos distintos admitidos. |
| FR-008–FR-009 | Historia 5.1–5.2, 5.5, Historia 6.1–6.4 y SC-005: ficha correcta, búsqueda y filtros combinados. |
| FR-010–FR-011 | Historia 5.3–5.4 y SC-013: acceso solo de gestores, iguales permisos y autor real. |
| FR-012–FR-013, FR-020 | Historia 2.1–2.6 y SC-006/SC-007/SC-012/SC-014: entrega, devolución, custodia y ubicación coherentes. |
| FR-014 | Historia 2.3, Historia 4.1 y SC-008: datos del movimiento y observación opcional. |
| FR-016–FR-017 | Historia 3.1–3.8 y SC-009/SC-014: original conservado, restauración y elegibilidad limitada. |
| FR-018 | Historia 4.1–4.4 y SC-010: cambio real de condición solo Disponible, con motivo. |
| FR-019 | Historia 1.5–1.6 y SC-011: custodios identificados, correo válido y único sin restringir dominio. |
| FR-022 | Historia 5.6 y SC-016: historial conservado sin borrado automático. |
| FR-023 | Casos límite y SC-015: integridad ante concurrencia y ausencia de cambios parciales. |
