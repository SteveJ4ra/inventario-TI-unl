# ADR-0304 · Persistencia de adquisición

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Anderson · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a 003/FR-007–FR-011, CA-05 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar persistencia de adquisición de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. mantener documento compartido y línea individual en PostgreSQL. Ventaja: Conserva una referencia compartida y valor por equipo. Limitación: Añade relaciones y validación transaccional.

B. duplicar datos de factura en cada activo. Ventaja y limitación: Consulta simple, pero facilita inconsistencias al corregir facturas.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Correcciones | Una referencia compartida evita repetir datos del documento | Cada copia debe mantenerse coherente |
| Valoración | La línea conserva el valor individual y la factura su total | Guardar solo el total por equipo confunde factura y valor individual |
| Pruebas | Se prueban relaciones, restricciones y rollback | Se requiere detectar divergencias entre copias de una misma factura |

## 6. Decisión propuesta y justificación

Se propone mantener documento compartido y línea individual en PostgreSQL. Esta opción responde a 003/FR-007–FR-011, CA-05 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Conserva una referencia compartida y valor por equipo. Negativa y compromiso: Añade relaciones y validación transaccional.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Inconsistencia entre altas parciales | Media | Medio | Crear activo y línea en una transacción |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a modelos de adquisición y servicios. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: 003/FR-007–FR-011, CA-05. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

## 11. Evidencia de implementación

El estado propuesto corresponde al trabajo local de semana 3. El enlace a commit o PR se añadirá cuando exista.

## 12. Referencias

- https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- https://c4model.com/
- `docs/semana-2/dossier-requisitos.md` y especificaciones 002–008 del proyecto.

## 13. Historial

| Fecha | Cambio |
| --- | --- |
| 2026-11-05 | Propuesta elaborada para revisión. |
