# Especificación: control de lotes de licencias de software

**Rama propuesta:** feature/anderson-006-lotes-licencias
**Identificador:** 006-lotes-licencias
**Creado:** 1 de noviembre de 2026
**Estado:** especificación preparada; no implementada.
**Decisiones:** DBE-030 a DBE-032 y DBE-044.

## Descripción

Permitir inventariar licencias agrupadas por compra/lote para productos con un número finito de puestos por usuario o dispositivo. No se asigna cada puesto a una persona ni a un equipo. El sistema conserva cantidad comprada y cantidad actualmente en uso introducida por el gestor; los remanentes son la diferencia. Fechas permiten identificar si el lote está por iniciar, vigente o vencido.

## Historias y aceptación

### US1 — Registrar un lote de licencias (P1)

Como gestor, quiero registrar producto, proveedor, tipo, cantidad y vigencia para conocer el tamaño de cada licencia institucional.

1. Cada fila representa un lote, no una clave ni un asiento individual.
2. Se exige producto, proveedor, tipo por usuario/dispositivo, cantidad comprada, cantidad en uso válida y fecha de inicio (siempre obligatoria).
3. La fecha de fin es opcional; sin ella no vence automáticamente.
4. No se guardan claves de activación, facturas ni destinatarios individuales.

### US2 — Consultar y actualizar cantidades (P1)

Como gestor, quiero consultar remanentes y ajustar el uso agregado conservando quién cambió las cifras.

1. Remanentes = cantidad comprada − cantidad en uso.
2. Cantidad en uso no puede superar compradas ni ser negativa.
3. Al editar se registra autor, fecha/hora y antes/después.
4. Un lote vencido conserva el conteo de remanentes, pero se muestra como Vencido; el conteo no afirma que el puesto vencido sea utilizable.
5. El sistema calcula estado temporal desde fechas: Por iniciar, Vigente o Vencido.

## Requisitos funcionales

- FR-001: Registrar y consultar lotes de licencia de software sin asociarlos individualmente a activos/personas.
- FR-002: Registrar producto, proveedor y modalidad de puestos finitos por usuario o dispositivo.
- FR-003: Registrar cantidad comprada y cantidad en uso como enteros no negativos.
- FR-004: Calcular remanentes = compradas − en uso; rechazar cantidad en uso > compradas.
- FR-005: Exigir fecha de inicio de vigencia; fecha de fin opcional.
- FR-006: Derivar estado Por iniciar/Vigente/Vencido a partir de fechas, sin borrar el lote.
- FR-007: Mostrar remanentes aun si está vencido y distinguirlos de disponibilidad vigente.
- FR-008: Permitir edición auditada de los campos de lote y cantidades; preservar autor, fecha/hora y antes/después.
- FR-009: No guardar claves de activación, licencias ilimitadas/de campus o asignaciones individuales.
- FR-010: Gestores autorizados tienen mismos permisos; operaciones sujetas a sesión, CSRF y validación del servidor.
- FR-011: El listado permite buscar producto/proveedor y filtrar tipo/estado para localizar el lote.
- FR-012: No relacionar una licencia con el registro de adquisición de activos físicos en este alcance.

## Criterios de éxito

- SC-001: Para un lote de 10 puestos con 4 en uso se muestran 6 remanentes.
- SC-002: Un lote con cantidad en uso mayor que comprada se rechaza sin cambios.
- SC-003: Un lote con fecha de fin pasada muestra Vencido y conserva el conteo remanente.
- SC-004: No se permite fecha de inicio vacía; fecha de fin sí puede omitirse.
- SC-005: Edición de cantidad permite reconstruir valores anterior/nuevo, autor y fecha.

## Límites

No se incluye compra/renovación, aprobación de software, cumplimiento contractual, claves, instalación automática, asignación a personas/equipos, licencias de campus/ilimitadas, facturación ni integración con proveedores.
