# ADR-0301 · Modularidad del backend

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Alex · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a 002/FR-001, RNF-04 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar modularidad del backend de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. organizar código en módulos de la aplicación Django con servicios explícitos. Ventaja: Menor complejidad operativa y transacciones locales. Limitación: Se requiere disciplina de límites y revisión de dependencias.

B. separar cada capacidad en servicios desplegables independientes. Ventaja y limitación: Mayor autonomía de despliegue, pero añade red, autenticación y consistencia distribuida.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Transacciones | Una base permite coordinar activo y movimiento en una transacción | Dividir persistencia obliga a coordinar operaciones distribuidas |
| Operación | Un despliegue del backend y una conexión a PostgreSQL | Varios despliegues, comunicaciones y controles de acceso |
| Pruebas | Las suites existentes ejercitan módulos y recorridos integrados | Requiere además contratos y fallos de comunicación entre servicios |

## 6. Decisión propuesta y justificación

Se propone organizar código en módulos de la aplicación Django con servicios explícitos. Esta opción responde a 002/FR-001, RNF-04 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Menor complejidad operativa y transacciones locales. Negativa y compromiso: Se requiere disciplina de límites y revisión de dependencias.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Dependencias cruzadas entre módulos | Media | Medio | Revisar imports y mantener pruebas por flujo |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a componentes API, servicios y modelos. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: 002/FR-001, RNF-04. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

## 11. Evidencia de implementación

El estado propuesto corresponde al trabajo local de semana 3. El enlace a commit o PR se añadirá cuando exista.

## 12. Referencias

- https://docs.djangoproject.com/en/5.2/intro/reusable-apps/
- https://c4model.com/
- `docs/semana-2/dossier-requisitos.md` y especificaciones 002–008 del proyecto.

## 13. Historial

| Fecha | Cambio |
| --- | --- |
| 2026-11-05 | Propuesta elaborada para revisión. |
