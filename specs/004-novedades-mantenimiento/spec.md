# Especificación: novedades, pérdida, recuperación y mantenimiento

**Rama propuesta:** feature/novedades-mantenimiento
**Identificador:** 004-novedades-mantenimiento
**Creado:** 1 de noviembre de 2026
**Estado:** especificación preparada; no implementada.
**Decisiones:** DBE-012 a DBE-021 en ../../docs/sdd/decisiones-alcance-backend.md.

## Descripción

Registrar daños/observaciones, pérdida/robo, recuperación y trabajos de mantenimiento que ya comenzaron. La ficha distingue condición física de asignación y localización. Cada novedad conserva autoría e historial; el equipo no aparece como disponible mientras esté No localizado o tenga mantenimiento En curso.

## Historias y aceptación

### US1 — Registrar y resolver daños u observaciones (P1)

Como gestor, quiero registrar una novedad para señalar que un activo tiene un daño u observación pendiente de atención.

1. Un gestor registra descripción, tipo daño/observación y autor/fecha generados por el servidor.
2. Se permite registrar la novedad aunque el activo esté Asignado; la ficha muestra alerta pendiente.
3. La novedad no cambia automáticamente condición, asignación ni ubicación.
4. El gestor resuelve la novedad con nota obligatoria; el sistema guarda autor/fecha de resolución y conserva la alerta en historial.

### US2 — Iniciar y cerrar mantenimiento (P1)

Como gestor, quiero registrar el envío real a un taller y el resultado al terminar, evitando una agenda futura.

1. El mantenimiento comienza para un activo localizado y Disponible; si estaba asignado, primero se registra la devolución.
2. Al iniciar se registra descripción, ubicación/taller, autor y fecha; el activo queda con mantenimiento En curso y no puede entregarse aunque siga Operativo.
3. El cambio a En reparación, si corresponde, se registra por la operación de condición existente, separado del evento de mantenimiento.
4. Al cerrar se exige resultado, fecha y ubicación de recepción. Se preselecciona la ubicación previa al taller; el gestor puede corregirla y confirma explícitamente antes de guardar.
5. El cierre no cambia automáticamente la condición.
6. Un activo No localizado durante mantenimiento interrumpe el mantenimiento sin resultado de reparación. Si se recupera, se abre un nuevo mantenimiento para continuar.

### US3 — Reportar pérdida o robo y recuperación (P1)

Como gestor, quiero marcar un activo No localizado, conservar su último estado y registrar recuperación si vuelve a aparecer.

1. Se permite reportar pérdida o robo sobre activo Disponible, Asignado o en mantenimiento.
2. El reporte marca No localizado y guarda último estado de localización, condición, asignación, ubicación, custodio conocido y mantenimiento en curso, si existían.
3. No se crea una devolución ficticia ni se marca automáticamente la baja.
4. Mientras esté No localizado, no puede entregarse ni registrarse como disponible; la ficha destaca su estado y último custodio conocido.
5. La recuperación exige inspección, nueva condición y ubicación; conserva el código, cierra el reporte y deja el activo localizado, Disponible y sin custodio vigente.
6. La recuperación no reactiva automáticamente un mantenimiento interrumpido.

## Requisitos funcionales

- FR-001: Registrar novedad por daño/observación con descripción, tipo, fecha/hora y gestor autor.
- FR-002: Permitir novedad de daño/observación en activo Disponible o Asignado y mostrar alerta hasta su resolución.
- FR-003: Resolver novedad con nota obligatoria, gestor y fecha/hora; conservarla en el historial.
- FR-004: No cambiar condición automáticamente por una novedad; usar el flujo de condición existente para cambios reales.
- FR-005: Iniciar mantenimiento para activo localizado, Disponible, sin custodia actual y sin otro mantenimiento En curso.
- FR-006: Guardar al inicio descripción, ubicación/taller, autor, fecha/hora y ubicación previa.
- FR-007: Bloquear entregas mientras exista mantenimiento En curso, aunque la condición sea Operativo.
- FR-008: Cerrar mantenimiento exigiendo resultado y ubicación de recepción; proponer ubicación previa y solicitar confirmación explícita antes de guardar.
- FR-009: Mantener separado el evento de mantenimiento del cambio de condición.
- FR-010: Registrar pérdida/robo con tipo, descripción, autor, fecha/hora y snapshots de ubicación, condición, asignación, custodio y mantenimiento previo.
- FR-011: Cambiar situación del activo a No localizado; bloquear entrega, devolución como si estuviera físicamente presente y cierre normal de mantenimiento.
- FR-012: Al reportar No localizado durante mantenimiento, marcar dicho evento Interrumpido por No localizado, sin resultado. Al recuperar, cualquier continuación usa un evento nuevo.
- FR-013: Registrar recuperación con condición y ubicación nuevas, conservar código e historial y dejar Disponible/sin custodio vigente.
- FR-014: No dar de baja automáticamente un activo No localizado.
- FR-015: Preservar eventos originales y resolver conflictos concurrentes sin cambios parciales.
- FR-016: Conservar toda novedad, mantenimiento, reporte y recuperación sin borrado automático.

## Criterios de éxito

- SC-001: Una novedad creada en activo Asignado deja alerta sin cambiar su condición ni custodio.
- SC-002: Un mantenimiento En curso bloquea entrega hasta cierre o interrupción.
- SC-003: El cierre conserva ubicación previa, ubicación confirmada, resultado, autor y fecha.
- SC-004: Un robo durante mantenimiento deja el activo No localizado, conserva taller/condición/último custodio y marca mantenimiento interrumpido.
- SC-005: La recuperación conserva código e historial, exige inspección y no crea una devolución inventada.

## Límites

No se incluyen calendario de mantenimientos, órdenes futuras, proveedores/costos, flujo de aprobación de reparación, traslado independiente, denuncias externas ni adjuntos. La ubicación se registra como texto libre con sugerencias de valores anteriores; no se administra un catálogo de ubicaciones.