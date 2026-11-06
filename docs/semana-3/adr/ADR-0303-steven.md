# ADR-0303 · Versionado y contrato de respuestas

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Steven · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a HU-01–HU-02, RNF-05 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar versionado y contrato de respuestas de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. introducir /api/v1/ para el flujo elegido conservando /api/. Ventaja: Permite migrar sin romper clientes actuales. Limitación: Se mantienen temporalmente dos contratos.

B. cambiar las respuestas de /api/ directamente. Ventaja y limitación: Evita duplicar rutas, pero rompe clientes y pruebas existentes.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Compatibilidad | Los clientes existentes conservan ruta y representación | Los consumidores deben migrar en el mismo cambio |
| Contrato | v1 introduce el sobre JSON en un alcance explícito | Cambiar la representación altera todas las llamadas antiguas |
| Mantenimiento | Debe comprobarse que ambas entradas preserven reglas comunes | Un contrato único reduce versiones, con mayor costo de migración inicial |

## 6. Decisión propuesta y justificación

Se propone introducir /api/v1/ para el flujo elegido conservando /api/. Esta opción responde a HU-01–HU-02, RNF-05 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Permite migrar sin romper clientes actuales. Negativa y compromiso: Se mantienen temporalmente dos contratos.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Divergencia entre versiones | Media | Medio | Pruebas de compatibilidad y documentación de alcance |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a adaptador v1 y API. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: HU-01–HU-02, RNF-05. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

## 11. Evidencia de implementación

El estado propuesto corresponde al trabajo local de semana 3. El enlace a commit o PR se añadirá cuando exista.

## 12. Referencias

- https://www.django-rest-framework.org/api-guide/versioning/
- https://c4model.com/
- `docs/semana-2/dossier-requisitos.md` y especificaciones 002–008 del proyecto.

## 13. Historial

| Fecha | Cambio |
| --- | --- |
| 2026-11-05 | Propuesta elaborada para revisión. |
