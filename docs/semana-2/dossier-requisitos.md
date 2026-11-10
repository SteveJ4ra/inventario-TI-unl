# Dossier de requisitos · Semana 2

Base del proyecto: develop cbb632d. Revisión de las especificaciones 002–008 y de las decisiones registradas en docs/sdd/decisiones-alcance-backend.md. Las decisiones representan el alcance académico acordado y requieren contraste con el equipo y el docente.

## Problema y alcance

El proyecto necesita identificar individualmente activos de TI, conocer su ubicación y custodia y conservar los hechos que explican su situación. El alcance acordado comprende activos físicos y adquisiciones, custodios, entregas y devoluciones, novedades, pérdida y recuperación, mantenimiento, bajas, licencias finitas, QR e importación de activos y licencias. La integración institucional queda fuera.

| Actor | Necesidad | Acceso previsto |
| --- | --- | --- |
| Gestor | Registrar y consultar activos y movimientos | Operar el inventario con cuenta autorizada |
| Custodio | Tener identificada la custodia temporal | Persona registrada sin cuenta de acceso |
| Revisor | Examinar solicitudes de baja asignadas | Decidir solicitudes de otra facultad con acceso limitado |
| Operador técnico | Mantener facultades y cuentas revisoras | Administrar las funciones autorizadas |

## Historias y criterios de aceptación

| ID | Historia | Criterios verificables | Fuente |
| --- | --- | --- | --- |
| HU-01 | Como gestor quiero registrar cada activo para identificarlo de forma estable. | Dado un alta válida, cuando se guarda, entonces se genera un código TI único y el activo queda disponible sin custodio. | 002 Historia 1 y FR-002, FR-015 |
| HU-02 | Como gestor quiero registrar la entrega y devolución para conocer la custodia y conservar el historial. | Dado un activo disponible y operativo, cuando se entrega, queda asignado. Al devolverlo se registra la condición y queda disponible sin custodio. | 002 Historia 2, FR-012 y FR-013 |
| HU-03 | Como gestor quiero corregir la última operación elegible para conservar el antecedente y restaurar la situación previa. | Dado un movimiento elegible, cuando se rectifica con motivo, se conserva el original y se restaura el estado anterior. Se rechaza si existe un evento posterior. | 002 Historia 3, FR-016 y FR-017; contratos transversales |
| HU-04 | Como gestor quiero documentar la adquisición para relacionar cada equipo con su compra o donación. | Una factura puede vincular varios activos, conserva su total y cada activo su valor individual. Una donación guarda respaldo textual y valor estimado por activo. | 003 US1–US2, FR-007–FR-011 |
| HU-05 | Como gestor quiero registrar una novedad para advertir un daño sin perder su historial. | Una novedad pendiente muestra alerta y no cambia automáticamente la condición. Al resolverla se exige nota y se conserva el antecedente. | 004 US1, FR-001–FR-004 |
| HU-06 | Como gestor quiero registrar un mantenimiento para conocer el taller y evitar entregas durante la intervención. | Dado un mantenimiento en curso, se rechaza la entrega. Al cerrarlo se exige resultado y ubicación confirmada. | 004 US2, FR-005–FR-009 |
| HU-07 | Como gestor quiero reportar pérdida o robo y registrar una recuperación para mantener la trazabilidad del activo. | El reporte conserva el último estado y deja el activo no localizado. La recuperación exige inspección y lo deja disponible sin custodio. | 004 US3, FR-010–FR-014 |
| HU-08 | Como gestor quiero dar de baja un activo elegible para registrar su retiro con motivo e historial. | Un activo localizado y disponible puede darse de baja sin custodia ni mantenimiento activo. Se conserva la ficha. | 005 US1, FR-001–FR-004 |
| HU-09 | Como revisor quiero decidir una solicitud asignada de otra facultad para documentar la revisión independiente. | Se rechaza autoaprobación y revisor de la misma facultad. Al rechazar se exige motivo. Recuperar el activo cancela una solicitud pendiente. | 005 US2, FR-005–FR-010 |
| HU-10 | Como gestor quiero controlar lotes de licencias para conocer cantidades adquiridas, en uso y remanentes. | El remanente es cantidad comprada menos cantidad en uso. Se rechaza que el uso exceda la compra. | 006 US1–US2 y spec.md |
| HU-11 | Como gestor quiero escanear un QR para abrir la ficha protegida del activo. | El QR contiene enlace con código TI y la ficha exige sesión de gestor. | 007 US1, FR-001–FR-006 |
| HU-12 | Como gestor quiero importar un lote de activos o licencias para registrar varios elementos con controles. | Una fila inválida impide aplicar todo el lote. Se exigen dos confirmaciones del mismo gestor y la aplicación es atómica. | 008 US1–US3, FR-001–FR-007 |

## Requisitos no funcionales para verificación

| ID | Atributo | Condición verificable | Evidencia prevista |
| --- | --- | --- | --- |
| RNF-01 | Acceso | Una cuenta sin permiso no puede ejecutar operaciones restringidas ni leer solicitudes ajenas. | Pruebas de permisos por rol y objeto |
| RNF-02 | Integridad | Una operación rechazada o una importación fallida no deja escrituras parciales. | Pruebas transaccionales con PostgreSQL |
| RNF-03 | Auditabilidad | Los eventos acordados conservan autor, fecha y antecedentes y no se reescriben. | Consulta de historial y pruebas de inmutabilidad |
| RNF-04 | Reproducibilidad | Un entorno preparado siguiendo instrucciones puede ejecutar migraciones y pruebas. | README y comandos ejecutados |
| RNF-05 | Interoperabilidad | El contrato API documenta métodos, cuerpos, validaciones y códigos HTTP utilizados. | Contrato y pruebas HTTP; OpenAPI pendiente de consolidar |

## Matriz de trazabilidad inicial

| Necesidad / actor | Historia | Requisito | Aceptación | Evidencia |
| --- | --- | --- | --- | --- |
| Identificar equipo / gestor | HU-01 | 002/FR-002, FR-015 | Código único y alta disponible | 002 spec Historia 1; tests de activos |
| Controlar custodia / gestor | HU-02 | 002/FR-012–FR-014 | Entrega válida y devolución con historial | 002 spec Historia 2; tests de movimientos |
| Corregir error / gestor | HU-03 | 002/FR-016–FR-017 | Original conservado y restauración | 002 Historia 3; tests de rectificación |
| Respaldar adquisición / gestor | HU-04 | 003/FR-007–FR-011 | Documento compartido y valor individual | 003 US1–US2; tests de adquisiciones |
| Informar daño / gestor | HU-05 | 004/FR-001–FR-004 | Alerta y resolución auditada | 004 US1; tests de incidentes |
| Controlar taller / gestor | HU-06 | 004/FR-005–FR-009 | Bloqueo de entrega durante intervención | 004 US2; tests de mantenimiento |
| Registrar pérdida / gestor | HU-07 | 004/FR-010–FR-014 | Estado no localizado y recuperación | 004 US3; tests de recuperación |
| Retirar / gestor | HU-08 | 005/FR-001–FR-004 | Baja con motivo e historial | 005 US1; tests de integración de baja |
| Revisar / revisor | HU-09 | 005/FR-005–FR-010 | Independencia y cancelación al recuperar | 005 US2; tests de contrato e integración |
| Controlar puestos / gestor | HU-10 | 006/FR-003–FR-005 | Remanente y límite de uso | 006 historias; tests de licencias |
| Abrir ficha / gestor | HU-11 | 007/FR-001–FR-006 | QR sin datos personales y acceso protegido | 007 US1; tests QR |
| Cargar lote / gestor | HU-12 | 008/FR-001–FR-007 | Validación total y dos confirmaciones | 008 US3; tests CSV |

La tabla presenta los requisitos principales por historia. El archivo requisitos-funcionales.md contiene el inventario completo de requisitos funcionales con enlaces a sus especificaciones. La tabla evidencia-pruebas.md identifica pruebas concretas para estos recorridos. La asociación exhaustiva de cada FR con una prueba se completará conforme avance la verificación.

La entrada consolidada de la especificación está en [specification.md](specification.md). Los documentos se publicarán en docs/semana-2.

## Contratos HTTP de referencia

| Necesidad | Método y ruta existente | Entrada | Resultado |
| --- | --- | --- | --- |
| Consultar activos | GET /api/assets/ | búsqueda y filtros opcionales | lista paginada |
| Registrar activo | POST /api/assets/ | datos de ficha y adquisición | 201 con activo creado |
| Registrar entrega | POST /api/assets/{id}/deliver/ | custodio, destino y expected_revision | movimiento creado o rechazo |
| Solicitar baja | POST /api/assets/{id}/retirement-requests/ | motivo, revisor y expected_revision | solicitud creada o rechazo |
| Descargar QR | GET /api/assets/{id}/qr.svg | sesión de gestor | imagen SVG |

Las rutas y errores se deben contrastar con el código y cada contrato. La API actual usa /api/ y el examen solicita versionado y contrato común. Su adaptación queda pendiente de una decisión técnica y pruebas de compatibilidad.

## Observación sobre filtros

Tras la observación del docente sobre la cantidad de filtros, definimos simplificar la consulta visual. Se propone mantener una búsqueda general y mostrar tres filtros principales: categoría, situación del activo y condición. La situación distinguirá Disponible, Asignado, No localizado y Baja. La condición mantendrá Operativo, Averiado y En reparación. La búsqueda general seguirá admitiendo código, nombre, marca, modelo, serie y nombre o correo del custodio.

La especificación 002/FR-009 y la API en cbb632d mantienen los filtros originales de categoría, condición, asignación, ubicación y custodio. La simplificación está implementada y documentada en una rama local de trabajo; su integración en develop se realizará mediante el PR correspondiente. Los parámetros anteriores de la API se conservan para mantener compatibilidad.

## Escenarios de aceptación y fuentes de decisión

| Criterio | Precondición y acción | Resultado esperado | Fuente |
| --- | --- | --- | --- |
| CA-01 | Gestor registra datos válidos | Código TI único, disponible y sin custodio | 002 Historia 1; DEC-018 y DEC-029 |
| CA-02 | Gestor intenta entregar un activo asignado o averiado | Se rechaza sin nuevo movimiento | 002 Historia 2; DEC-019 |
| CA-03 | Gestor devuelve un activo asignado e informa condición y recepción | Disponible sin custodio, con antecedente | 002 Historia 2; DEC-020 |
| CA-04 | Gestor rectifica una operación antigua con eventos posteriores | Se rechaza la rectificación | 002 Historia 3; DEC-023 y DEC-024 |
| CA-05 | Gestor registra dos activos de una factura | Documento común e importes individuales | 003 US1; DBE-007 y DBE-008 |
| CA-06 | Gestor registra una novedad de daño de un activo asignado | Alerta visible sin modificar custodia o condición | 004 US1; DBE-012 y DBE-013 |
| CA-07 | Gestor intenta entregar durante mantenimiento activo | Operación rechazada | 004 US2; DBE-018 |
| CA-08 | Gestor informa pérdida y después recupera con inspección | Historial conservado; disponible y sin custodio | 004 US3; DBE-016 y DBE-017 |
| CA-09 | Gestor solicita baja de activo asignado localizado | Baja normal rechazada hasta devolución | 005 US1; DBE-022 |
| CA-10 | Revisor intenta aprobar su propia solicitud o la de la misma facultad | Decisión rechazada | 005 US2; DBE-023 y DBE-025 |
| CA-11 | Lote tiene 10 puestos y 4 en uso | Remanente de 6, incluso si está vencido | 006 US2; DBE-032 y DBE-044 |
| CA-12 | Gestor descarga QR | SVG con enlace y código, sin datos personales | 007 US1–US2; DBE-033 |
| CA-13 | CSV contiene una fila inválida | Se muestran errores y no se crea ningún registro | 008 US3; DBE-035 y DBE-036 |
| CA-14 | Otro gestor intenta confirmar la carga iniciada por un tercero | Confirmación rechazada | 008 US3; DBE-049 |

## Evolución de requisitos

Las decisiones iniciales incluían un custodio obligatorio para toda alta. El grupo aclaró que el custodio representa una asignación temporal y que el registro comienza sin custodio (DEC-007, DEC-014 y DEC-018). El estado inicialmente planteado se separó en condición y asignación (DEC-012). La consulta evolucionó desde los filtros documentados en DEC-028 hacia la propuesta de simplificación motivada por la observación docente.

## Declaración de herramientas

Utilizamos Codex como apoyo para organizar la información. Contrastamos las historias con las especificaciones, el registro de decisiones y las pruebas existentes.

## Clarificaciones y riesgos

Se acordó que solo equipos disponibles y operativos pueden entregarse, que la baja por pérdida o robo requiere revisión independiente y que el lote CSV se procesa completo o nada. Quedan por revisar la integración institucional, plazos de conservación, formato de documentación final y fuentes institucionales reales. El CSV de una donación nueva tiene una limitación documentada en las pruebas actuales.

## Referencias

1. Grupo 5, AA1, ACD1 y APE1, entregas proporcionadas.
2. Repositorio, specs/002-registro-consulta-activos a specs/008-importacion-csv, y docs/sdd/decisiones-alcance-backend.md, revisión cbb632d.
3. Fielding et al., RFC 9110, HTTP Semantics, https://www.rfc-editor.org/rfc/rfc9110.html.
4. GitHub, Spec Kit, https://github.com/github/spec-kit.

## Fuentes y métodos de verificación de los requisitos no funcionales

| Requisito | Fundamento del proyecto | Prueba o método de verificación |
| --- | --- | --- |
| RNF-01 | 002/FR-010; 005/FR-007 y FR-013 | backend/inventory/tests/test_permissions.py y contract_tests/test_api.py comprueban permisos y acceso de revisores |
| RNF-02 | 002/FR-023; 008/FR-003 y FR-007 | test_concurrency.py, test_import_acquisitions.py y test_license_lots.py comprueban carreras y rollback |
| RNF-03 | 002/FR-014, FR-016 y FR-022; 003/FR-002 | test_rectification.py y test_metadata_edit.py comprueban conservación y auditoría |
| RNF-04 | Constitution IV–V y backend/README.md | Preparar el entorno documentado y ejecutar migraciones y suites en PostgreSQL temporal |
| RNF-05 | Contratos 002–008 y RFC 9110 | Comparar métodos, datos y respuestas del contrato con las pruebas API. La documentación OpenAPI se completa en la semana 3 |

## Participación y revisión

El dossier se mantiene como documento común del grupo. Cada integrante puede vincular a su entrega la contribución o revisión que realizó y explicar su relación con los requisitos.
