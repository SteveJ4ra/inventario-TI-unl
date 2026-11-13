# ADR-0303 · Versionado y contrato de respuestas

| Campo | Valor |
| --- | --- |
| Código ADR | ADR-0303 |
| Estado | Propuesto |
| Título | Versionado y contrato de respuestas |
| Fecha | 2026-11-05 |
| Proyecto | Inventario TI UNL |
| Responsable | Steven Jumbo |
| Requisitos relacionados | RNF-05, 002/FR-002, FR-009 y FR-012 a FR-015, HU-01 y HU-02 |
| Versión | 1.2 |

## 1. Contexto

El recorrido de alta, consulta, entrega y devolución de activos necesitaba un formato JSON uniforme. Los clientes existentes ya consumían /api/. El incremento debía conservar la compatibilidad con esos clientes, reutilizar las reglas del backend Django y mantener el flujo de HU-01 y HU-02. RNF-05 pide documentar métodos, cuerpos, validaciones y códigos HTTP para facilitar la interoperabilidad; la compatibilidad con rutas anteriores es una restricción adicional de esta decisión.

## 2. Problema de decisión

¿Qué estrategia de versionado permite introducir una respuesta JSON uniforme y conservar la compatibilidad de los clientes actuales?

## 3. Criterios de decisión

Compatibilidad de rutas y respuestas, reutilización de reglas, facilidad de prueba y costo de mantenimiento.

## 4. Alternativas consideradas

**A. Incorporar /api/v1/ y conservar /api/.** El adaptador v1 presenta el nuevo formato de respuesta y reutiliza las reglas existentes. Facilita una adopción gradual. Mantener ambas entradas exige pruebas de compatibilidad y trae el riesgo de que las respuestas diverjan.

**B. Cambiar el contrato de /api/ en las rutas existentes.** Deja una sola versión del contrato después de migrar. Requiere coordinar el cambio con los consumidores actuales. El riesgo es que fallen clientes que todavía esperan el formato anterior.

## 5. Comparación

| Criterio | A. Incorporar /api/v1/ | B. Cambiar /api/ |
| --- | --- | --- |
| Requisitos funcionales | La nueva entrada conserva alta, consulta, entrega y devolución al reutilizar las operaciones existentes. | Puede conservar las funciones si las vistas migradas usan las mismas reglas. |
| Interoperabilidad | El contrato v1 documenta métodos, datos, validaciones y respuestas; también se mantiene el contrato anterior. | Un contrato actualizado puede documentar esos elementos, pero exige coordinar su adopción. |
| Compatibilidad | Conserva las rutas y el formato anteriores. | Los consumidores deben adaptar sus llamadas en el mismo cambio. |
| Mantenibilidad | Dos entradas comparten las reglas del backend. | Un formato reduce el mantenimiento después de migrar. |
| Testabilidad | Requiere comprobar la API v1 y el contrato previo. | Requiere comprobar la migración de los clientes y el nuevo contrato. |
| Riesgo | Diferencias de comportamiento entre versiones. | Interrupciones en clientes que dependan del formato anterior. |

## 6. Decisión

Se selecciona la **alternativa A** para el flujo priorizado de la semana 3. Django REST framework documenta el uso de rutas para distinguir versiones [1]. La separación permite introducir el formato uniforme en v1 y conservar el flujo de HU-01 y HU-02. Para atender RNF-05, el contrato debe documentar métodos, cuerpos, validaciones y respuestas HTTP; el versionado por sí solo no garantiza esa documentación.

## 7. Consecuencias

- **Positiva.** Los consumidores pueden adoptar el nuevo formato de manera gradual.
- **Negativa.** El equipo debe mantener y verificar dos contratos durante la transición.
- **Compromiso.** Las dos entradas reutilizan las reglas del backend. El alcance de v1 y la compatibilidad se comprueban con el contrato y las pruebas.

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
| --- | --- | --- | --- |
| Divergencia de reglas o respuestas entre versiones | Media | Medio | Reutilizar la lógica existente y ejecutar pruebas del recorrido y del contrato anterior. |

## 9. Impacto en la arquitectura

| Vista | Impacto |
| --- | --- |
| C1 | Se mantienen los actores del sistema. |
| C2 | El frontend sigue comunicándose con el backend Django, que utiliza PostgreSQL. |
| C3 | El adaptador v1 encamina las solicitudes y normaliza las respuestas según la separación de componentes de C4 [2]. [Diagrama C3](../c4-componentes.puml) |
| C4/UML | Las vistas y los servicios del flujo siguen representados en el [diagrama de clases](../flujo-clases.puml). |

**Responsabilidades y dependencias.** El enrutamiento dirige cada solicitud a su vista; el adaptador v1 traduce el contrato HTTP y la respuesta; los servicios aplican las reglas de inventario y los modelos representan los datos persistentes. El adaptador depende de los servicios: no debe duplicar las reglas de custodia ni escribir directamente el historial. Esta relación corresponde a la API, los servicios y la persistencia representados en C3.

**Componentes afectados.** Enrutamiento, adaptador v1 y API.

**Contratos afectados.** [Especificación de API v1](../especificacion-api-v1.md) y [OpenAPI del incremento](../openapi-v1.json).

## 10. Trazabilidad

| Elemento | Referencia |
| --- | --- |
| Requisitos | RNF-05, 002/FR-002, FR-009 y FR-012 a FR-015 |
| Historias de usuario | HU-01 y HU-02 |
| Criterios de aceptación | CA-01 a CA-03 y conservación de la compatibilidad de /api/ |
| Componente C4 | Adaptador v1 y API en C3 |
| Endpoint o contrato | /api/v1/assets/, su ficha por ID, las operaciones deliver y return, y las rutas previas bajo /api/ |
| Riesgo relacionado | Divergencia de reglas o respuestas entre versiones |
| Prueba relacionada | test_asset_cycle_and_legacy_contract, en test_api_v1.py |

Las relaciones entre requisitos, rutas y pruebas se detallan en la [matriz de trazabilidad de la semana 3](../trazabilidad.md).

## 11. Evidencia de implementación

| Evidencia | Enlace |
| --- | --- |
| Commit | [Incorporación de la API v1 y documentación principal](https://github.com/SteveJ4ra/inventario-TI-unl/commit/f84ab306ddab41b41866ea520f706d369aced0d2) |
| Pull request | [PR #25 · API v1 y documentación principal](https://github.com/SteveJ4ra/inventario-TI-unl/pull/25) |
| Plan y tareas | [Plan de trabajo de la semana 3](../plan-y-tareas.md) |
| Documentación | [Guía de API](../guia-api.md) y [especificación del flujo versionado](../especificacion-api-v1.md) |
| Prueba | [Recorrido y compatibilidad del contrato anterior](../../../backend/inventory/tests/test_api_v1.py#L23) |

## 12. Referencias

[1] Django REST framework, “Versioning,” API Guide. [En línea]. Disponible en: [https://www.django-rest-framework.org/api-guide/versioning/](https://www.django-rest-framework.org/api-guide/versioning/). [Consulta: 12 nov. 2026].

[2] S. Brown, “The C4 model for visualising software architecture,” C4 model. [En línea]. Disponible en: [https://c4model.com/](https://c4model.com/). [Consulta: 12 nov. 2026].

## 13. Historial de la decisión

| Fecha | Cambio | Responsable |
| --- | --- | --- |
| 2026-11-05 | Propuesta inicial, versión 1.0. | Steven Jumbo |
| 2026-11-12 | Versión 1.1. Ajuste a la plantilla y actualización de la evidencia de implementación. | Steven Jumbo |
| 2026-11-12 | Versión 1.2. Corrección de RNF-05 y ampliación de la comparación y las responsabilidades. | Steven Jumbo |
