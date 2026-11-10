# ADR-0305 · Autenticación de la aplicación web

Estado: Propuesto para revisión del equipo · Fecha: 2026-11-05 · Proyecto: Inventario TI · Perspectiva asignada: Pedro · Versión: 1.0

## 1. Contexto

El incremento gestiona activos físicos y custodia sobre Django, DRF y PostgreSQL. La decisión debe responder a 002/FR-010, RNF-01 y permitir verificar el recorrido de alta, consulta, entrega y devolución.

## 2. Problema de decisión

¿Cómo organizar autenticación de la aplicación web de modo verificable y compatible con el sistema existente?

## 3. Criterios

Cumplimiento de requisitos, seguridad, mantenibilidad, testabilidad, complejidad de integración y costo de evolución.

## 4. Alternativas consideradas

A. mantener sesión Django y protección CSRF. Ventaja: Reutiliza el control actual y evita migrar clientes existentes. Limitación: Exige gestionar cookies, orígenes y CSRF.

B. usar tokens bearer como mecanismo exclusivo. Ventaja y limitación: Puede servir a clientes externos, pero exige ciclo de vida seguro de tokens.

## 5. Comparación

| Criterio | Alternativa A | Alternativa B |
| --- | --- | --- |
| Navegador | Cookie de sesión y CSRF se integran con el acceso actual | Requiere definir almacenamiento y envío de bearer tokens |
| Revocación | Se aplica la sesión y el estado de usuario existentes | Debe definirse expiración, revocación o renovación del token |
| Integración | Conserva las comprobaciones y pruebas de acceso actuales | Necesita migrar clientes y comprobar ambos mecanismos durante la transición |

## 6. Decisión propuesta y justificación

Se propone mantener sesión Django y protección CSRF. Esta opción responde a 002/FR-010, RNF-01 y a las restricciones reales del proyecto. La aceptación corresponde al equipo; el estado propuesto no representa una decisión docente.

## 7. Consecuencias

Positiva: Reutiliza el control actual y evita migrar clientes existentes. Negativa y compromiso: Exige gestionar cookies, orígenes y CSRF.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad estimada | Impacto estimado | Mitigación |
| --- | --- | --- | --- |
| Escritura sin protección CSRF | Media | Medio | Probar sesión y rechazo de escrituras sin token |

## 9. Impacto en arquitectura

C1 mantiene a gestores, revisores y operadores; C2 conserva web, backend y PostgreSQL. En C3 afecta a sesión, permisos y API. El UML de semana 3 muestra los elementos del flujo.

## 10. Trazabilidad

Requisitos y criterios: 002/FR-010, RNF-01. Proceso: `../proceso-principal.md`. Componentes: `../c4-componentes.puml`. API y prueba del recorrido: `backend/inventory/urls_v1.py` y `backend/inventory/tests/test_api_v1.py`.

## 11. Evidencia de implementación

El estado propuesto corresponde al trabajo local de semana 3. El enlace a commit o PR se añadirá cuando exista.

## 12. Referencias

- https://www.django-rest-framework.org/api-guide/authentication/
- https://c4model.com/
- `docs/semana-2/dossier-requisitos.md` y especificaciones 002–008 del proyecto.

## 13. Historial

| Fecha | Cambio |
| --- | --- |
| 2026-11-05 | Propuesta elaborada para revisión. |
