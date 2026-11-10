# Proceso principal: entregar y devolver un activo

## Análisis textual previo al diagrama

| Elemento | Definición |
|---|---|
| Propósito | Conservar quién entrega, quién recibe temporalmente, dónde está el activo y cómo regresa, sin sobrescribir antecedentes. |
| Participantes | Gestor autenticado y backend; el custodio participa físicamente, sin cuenta ni portal. |
| Inicio | Activo registrado con adquisición y facultad; código TI automático. |
| Entradas | Activo, revisión consultada, custodio y destino; al devolver: revisión, condición recibida y ubicación de recepción. |
| Datos | Asset, Custodian, Movement y sus instantáneas/autor; AcquisitionDocument y AcquisitionLine respaldan el alta. |
| Precondición de entrega | Localizado, Disponible, Operativo, sin mantenimiento activo; custodio existente y revisión vigente. |
| Precondición de devolución | Custodia activa y revisión vigente; una pérdida no produce una devolución ficticia. |
| Decisiones | Validar entrega y devolución; las salidas negativas no alteran el inventario. |
| Resultado | Entrega: Asignado con custodio/destino. Devolución: Disponible sin custodio, condición/recepción registradas. |
| Excepciones | 400 entrada; 403 acceso/CSRF; 404 recurso; 409 revisión/estado. Tras conflicto se consulta antes de corregir. |
| Límite | Sin reservas, solicitudes de préstamo, aprobación de entregas ni portal de custodios. |

## Secuencia operativa

1. Consultar la ficha y conservar su revisión.
2. Registrar la entrega con custodio y destino.
3. Validar permisos, revisión y disponibilidad en servidor.
4. Guardar entrega y movimiento en una transacción; si falla, rechazar sin cambios.
5. Recibir físicamente el activo y registrar devolución, condición y recepción.
6. Validar custodia y revisión; ante conflicto, consultar y corregir.
7. Guardar devolución e historial; dejar Disponible y sin custodio.

Las tareas usan infinitivo y complemento; los eventos describen situaciones; las compuertas exclusivas separan resultados mutuamente excluyentes. Las calles distinguen operación humana y backend. El XML incluye BPMN DI para importarlo en un modelador. isExecutable=false declara un modelo documental, no un motor de procesos.

## Vistas y correspondencia técnica

Vista ejecutiva: consultar -> entregar -> recibir -> devolver. Vista operativa: BPMN con validaciones y excepciones. Vista técnica: POST /api/v1/assets/{asset_id}/deliver/ y return/ -> OperationView -> DeliveryInput/ReturnInput -> services.record_operation -> transacción/bloqueo -> Asset/Movement. C4 y UML describen esa realización.

| Paso | Contrato/componente | Prueba o evidencia |
|---|---|---|
| Consultar | GET /assets/{asset_id}/; AssetView | VersionedFlowTests.test_asset_cycle_and_legacy_contract |
| Entregar | POST /deliver/; DeliveryInput; record_operation | Ciclo v1, movimientos, permisos y concurrencia |
| Guardar antecedente | Asset + Movement, transaction.atomic | Contratos de persistencia y pruebas de movimientos |
| Devolver | POST /return/; ReturnInput; record_operation | Ciclo v1 y rechazo de devolución sin custodia |
| Rechazar sin mutación | ValidationError, PermissionDenied, Conflict | Errores v1 y CSRF estricto |

## Relación con otros procesos

Daños/observaciones generan alerta sin cambiar automáticamente la condición. Pérdida/robo pasa a No localizado y conserva referencias. El mantenimiento bloquea entregas y se interrumpe si desaparece el activo. La baja normal exige Disponible y mantenimiento cerrado; No localizado requiere aprobación de otro revisor/facultad. Estos procesos conservan las reglas 004/005 y no son devoluciones silenciosas del BPMN.
