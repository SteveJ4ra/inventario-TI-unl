# Contrato de interacción de la pantalla web

**Base:** historias 1–6 de [spec.md](../spec.md). **Estado:** implementado y comprobado localmente; evidencia en [validation.md](../validation.md). Textos visibles en español; interfaz adaptable, con etiquetas de formulario y navegación por teclado.

## Acceso

Pantalla de acceso con usuario y contraseña. Al iniciar se consulta la sesión. Sin sesión se muestra acceso, sin consultar datos de inventario. Un usuario sin permiso de gestor recibe un mensaje de acceso denegado. Cerrar sesión termina la sesión y limpia datos privados del estado del cliente.

No hay autorregistro ni acceso de custodios. Los gestores se preparan por comando administrativo documentado, con contraseña interactiva y sin credenciales predeterminadas en el repositorio.

## Registro y consultas

- Listado con código, nombre, categoría, condición, asignación y ubicación; acceso a ficha. Búsqueda y filtros por los criterios aprobados. Aplicar búsqueda/filtros reinicia la página a 1; limpiar criterios recupera el listado. Paginación conserva criterios.
- Registro de activo con nombre y descripción separados, categoría, marca, modelo, serie, ubicación y condición obligatorios. Mostrar asignación inicial Disponible fija y sin custodio; el código se muestra después de guardar.
- Registro de custodio con nombre/correo obligatorios y dependencia opcional; selección de custodio existente para entrega. No añadir edición o borrado de personas.
- Ficha con todos los datos del activo, custodio actual cuando exista, acciones permitidas e historial. Disponible sin custodio no implica Operativo: mostrar ambos campos por separado.

La API define los valores; la web muestra etiquetas como Portátil y En reparación. Marca/modelo/ubicación se escriben como texto. Los filtros de ubicación usan los valores actuales informados, sin convertirlos en un catálogo administrable.

## Acciones de custodia

| Acción | Cuándo se presenta | Formulario / resultado |
|---|---|---|
| Entregar | Disponible y Operativo | Custodio, destino, observación opcional; tras éxito actualizar ficha e historial. |
| Devolver | Asignado con custodio | Condición recibida, recepción, observación opcional; éxito deja Disponible sin custodio. |
| Cambiar condición | Disponible | Otra condición, motivo obligatorio y observación opcional; conserva ubicación. |
| Rectificar | rectifiable_movement_id presente | Mostrar original objetivo y efecto de restaurar situación anterior; motivo obligatorio y observación opcional. |

Una rectificación no abre edición del original. Tras anular, el gestor registra por separado una operación correcta si corresponde. Un evento ya rectificado y los anteriores nunca reciben una acción que el servidor considere inelegible.

Se envía la revisión de la ficha vista por el gestor. Al recibir conflicto se explica que la ficha cambió y se recarga para revisar antes de intentar otra vez; no se reenvía el movimiento automáticamente. Deshabilitar el botón mientras se envía evita repeticiones accidentales, sin sustituir las garantías del backend.

## Historial y errores

Presentar tipo, fecha/hora local, autor, custodio relacionado, condiciones/ubicaciones anterior y posterior, observación y motivo cuando corresponde. Distinguir original rectificado y rectificación vinculada; no ocultar el original. El historial de devolución conserva quién tenía el activo aunque la ficha ya no tenga custodio.

Estados explícitos: carga, lista vacía, búsqueda sin coincidencias, ficha inexistente, error de conexión y errores por campo. Un fallo de red después de enviar no anuncia éxito: consultar ficha/historial para comprobar antes de repetir conscientemente. Mensajes claros para duplicados, falta de permisos, CSRF y estado incompatible. No imprimir contraseñas ni respuestas sensibles en consola.

## Comprobación prevista

Testing Library: campos obligatorios, errores de API, búsqueda/filtros y ausencia de acciones incompatibles; formulario de rectificación con motivo y revisión. Navegador: crear activo/custodio, entregar, devolver, cambiar condición y rectificar; verificar autoría con dos gestores y recarga de un formulario obsoleto. La evidencia y los resultados se registrarán al implementar, sin declararlos ahora como ejecutados.
