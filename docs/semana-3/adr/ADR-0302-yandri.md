# ADR-0302 · Reglas de negocio y transacciones

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Yandri · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a 002/FR-012–FR-014, CA-02–CA-03 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar reglas de negocio y transacciones de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. concentrar operaciones en servicios de aplicación con transacciones. Ventaja: Las reglas son reutilizables y verificables desde distintos puntos. Limitación: Los servicios pueden crecer demasiado.

B. ubicar reglas y escrituras directamente en cada vista. Ventaja y limitación: Menos archivos al inicio, pero mayor duplicación y vistas acopladas.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Consistencia | El servicio concentra las transacciones del recorrido | Cada vista debe reproducir los límites transaccionales |
| Reutilización | API histórica y v1 llaman a los mismos servicios | Es más fácil duplicar validaciones y escrituras |
| Acoplamiento | Permite probar operaciones separadas de HTTP | Las reglas quedan vinculadas a las solicitudes y respuestas |

## 6. Decisión propuesta y justificación

Se propone concentrar operaciones en servicios de aplicación con transacciones. Esta opción responde a 002/FR-012–FR-014, CA-02–CA-03 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Las reglas son reutilizables y verificables desde distintos puntos. Negativa y compromiso: Los servicios pueden crecer demasiado.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Reglas duplicadas en vistas nuevas | Media | Medio | Revisar límites y pruebas de servicio y API |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a servicios y persistencia. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: 002/FR-012–FR-014, CA-02–CA-03. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

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
