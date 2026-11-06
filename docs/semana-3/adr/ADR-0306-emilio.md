# ADR-0306 · Documentación del contrato HTTP

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Emilio · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a RNF-05, HU-01–HU-02 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar documentación del contrato http de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. publicar OpenAPI del flujo versionado junto al código. Ventaja: Permite inspeccionar operaciones y esquemas. Limitación: Hay que comprobar que documento e implementación coincidan.

B. mantener únicamente una descripción narrativa de rutas. Ventaja y limitación: Menor mantenimiento inicial, pero dificulta validación y herramientas.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Precisión | Los esquemas y operaciones son inspeccionables por herramientas | La descripción narrativa depende de interpretación humana |
| Uso | Swagger UI permite explorar peticiones y respuestas | Los ejemplos deben trasladarse manualmente a un cliente HTTP |
| Deriva | Se compara el objeto servido con la exportación y las pruebas | No hay estructura formal para detectar diferencias del contrato |

## 6. Decisión propuesta y justificación

Se propone publicar OpenAPI del flujo versionado junto al código. Esta opción responde a RNF-05, HU-01–HU-02 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Permite inspeccionar operaciones y esquemas. Negativa y compromiso: Hay que comprobar que documento e implementación coincidan.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Desactualización de especificación | Media | Medio | Comprobar rutas y contrato mediante pruebas |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a adaptador v1 y documentación. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: RNF-05, HU-01–HU-02. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

## 11. Evidencia de implementación

El estado propuesto corresponde al trabajo local de semana 3. El enlace a commit o PR se añadirá cuando exista.

## 12. Referencias

- https://spec.openapis.org/oas/v3.1.0
- https://c4model.com/
- `docs/semana-2/dossier-requisitos.md` y especificaciones 002–008 del proyecto.

## 13. Historial

| Fecha | Cambio |
| --- | --- |
| 2026-11-05 | Propuesta elaborada para revisión. |
