# Flujo priorizado: registro y custodia de un activo

## Participantes y desencadenante

Un gestor autorizado incorpora al inventario un activo físico y, cuando corresponde, registra su entrega a un custodio y su devolución. El custodio es una persona registrada sin cuenta. Antes del alta deben existir la facultad responsable y el documento de adquisición; esos datos están disponibles mediante las operaciones existentes de `/api/`.

## Actividades y decisiones

1. Autenticar al gestor y obtener el token CSRF para escrituras con sesión.
2. Seleccionar facultad y documento de adquisición existentes.
3. Registrar datos obligatorios del activo, valor individual y fecha de adquisición o motivo de fecha desconocida.
4. Validar identidad y datos; rechazar entradas inválidas o duplicadas sin guardar cambios parciales.
5. Generar el código TI; conservar el activo disponible y sin custodio.
6. Consultar el activo por identificador o búsqueda de la colección.
7. Registrar o seleccionar una persona custodio.
8. Comprobar disponibilidad, condición operativa, ausencia de mantenimiento y revisión vigente; registrar entrega con custodio y destino.
9. Registrar devolución con condición y ubicación de recepción; dejar el activo disponible y sin custodio.
10. Consultar el historial de movimientos conservando autor, fecha y situación anterior.

## Datos, excepciones y resultado

Se utilizan la ficha, el documento, la facultad, el custodio, la ubicación, la condición y `expected_revision`. Una identidad duplicada, una revisión desactualizada, un activo no disponible o una entrada inválida producen rechazo. La sesión y el CSRF se verifican en operaciones protegidas. Al finalizar, la ficha indica la situación actual y el historial conserva la entrega y devolución.

## Trazabilidad

| Elemento | Referencia |
| --- | --- |
| Historias | HU-01 y HU-02, dossier de semana 2 |
| Requisitos | 002/FR-002, FR-012–FR-015; 003/FR-007–FR-011 |
| Criterios | CA-01 a CA-03, dossier de semana 2 |
| Código | `backend/inventory/views.py`, `services.py`, `acquisition_services.py` |
| Pruebas | `backend/inventory/tests/test_api_v1.py`, `test_custody.py` |

Este proceso relaciona los requisitos de identificación y custodia con los servicios y pruebas del incremento.
