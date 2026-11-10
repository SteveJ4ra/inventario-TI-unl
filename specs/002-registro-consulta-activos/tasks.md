# Tareas: registro, consulta y custodia de activos

**Fecha:** 2026-10-20. **Cierre técnico revisado:** 2026-11-01; evidencia en [validation.md](validation.md). **Rama:** feature/registro-consulta-activos. **Entrada:** spec.md, plan.md, research.md, data-model.md, contracts/ y quickstart.md de esta carpeta.

Las pruebas fueron solicitadas expresamente (FR-001); se escriben por riesgo y contrato antes de su implementación correspondiente. No se impone al grupo adoptar TDD como metodología. Las marcas indican trabajo comprobado, no mera creación de archivos.

Los tamaños, nulabilidad, enums y unicidad se transcriben en las tareas de modelos; los demás detalles técnicos siguen los contratos. No se añaden funcionalidades de negocio. Rutas relativas a la raíz del repositorio.

## Fase 1: preparación

Entorno reproducible y archivos privados excluidos de Git.

- [X] T001 Verificar la configuración existente y añadir node_modules/, dist/, coverage/, *.log y archivos temporales a `.gitignore`, conservando la excepción .env.example (FR-001, FR-010).
- [X] T002 Preparar React/TypeScript/Vite, Vitest/Testing Library y scripts dev/test/build con dependencias fijadas y lockfile en `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`; proxy /api y Node compatible según research.md (FR-001).

## Fase 2: fundamentos

Acceso de gestores, errores consistentes y pruebas PostgreSQL aisladas; bloquea las historias.

- [X] T003 Crear el módulo Django en `backend/inventory/apps.py`, `backend/inventory/__init__.py`, `backend/inventory/urls.py` y registrarlo en `backend/config/settings.py` y `backend/config/urls.py` (FR-001).
- [X] T004 Definir permiso de usuario activo en grupo Gestores, incluso para superusuario, y errores JSON 400/403/404/405/409 con fields opcional en `backend/inventory/permissions.py` y `backend/inventory/errors.py` (FR-010).
- [X] T005 Probar acceso anónimo/no gestor, usuario inactivo, login/logout y CSRF explícito mediante los endpoints de sesión, sin depender de modelos de inventario, en `backend/inventory/tests/test_permissions.py` (FR-010; SC-013).
- [X] T006 Implementar sesión/CSRF/me/login/logout en `backend/inventory/auth_views.py`, `backend/inventory/urls.py` y configuración CSRF de desarrollo en `backend/config/settings.py`; no guardar secretos o tokens en localStorage (FR-010).
- [X] T007 Preparar creación interactiva de gestores sin contraseña predeterminada en `backend/inventory/management/commands/create_gestor.py` y PostgreSQL temporal de pruebas loopback con credenciales efímeras y parada en finally en `backend/tools/test_postgres.py`; sin cambiar .env ni privilegios del rol actual (FR-010, FR-023).
- [X] T008 Preparar tipos, cliente fetch con sesión/CSRF y errores/cancelación, acceso/salida y shell privado en `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`; limpiar datos privados al salir (FR-001, FR-010).

## Fase 3: US1 — registrar activos (P1, primer incremento demostrable)

Registrar desde API/web, obtener código y consultar ficha mínima; custodios registrados sin cuenta. Prueba independiente: alta válida, duplicados, obligatorios y código estable con fixtures propios.

- [X] T009 [US1] Probar alta y lectura mínima, todos los obligatorios/enum/límites, normalización, correo sin restricción de dominio, duplicados, rechazo de campos reservados y CSRF de escrituras de activos/custodios en `backend/inventory/tests/test_assets.py`; probar formulario en `frontend/src/tests/registration.test.tsx` (FR-002–FR-007, FR-015, FR-019, FR-021; SC-001–SC-004, SC-011).
- [X] T010 [US1] Crear Custodian en `backend/inventory/models.py`: full_name «texto, 160», email «EmailField, 254», department «texto, 160» opcional; «Formato válido, obligatorio, sin whitelist de dominios» y correo único Lower(Trim(email)); no crea User (FR-019).
- [X] T011 [US1] Crear Asset en `backend/inventory/models.py`: name «texto, 160», description «texto, 2000», brand/model «texto, 120 cada uno», serial_number «texto, 160», location «texto, 240»; textos obligatorios no vacíos. category «computadora_escritorio, portatil, monitor, impresora, equipo_red, periferico»; condition «operativo, averiado, en_reparacion»; assignment «disponible, asignado». Código «texto único, hasta 32», current_custodian «FK Custodian nullable, PROTECT», created_by «FK User PROTECT», revision «entero no negativo», inicial 0. Alta Disponible/sin custodio; unicidad normalizada marca+modelo+serie y CHECK estado/custodio (FR-002–FR-007, FR-015, FR-021).
- [X] T012 [US1] Generar migración de Asset/Custodian y secuencia persistente NO CYCLE para TI- con mínimo seis dígitos en `backend/inventory/migrations/0001_initial.py` y `backend/inventory/migrations/0002_integrity.py`; asignar código en servicio de alta atómico en `backend/inventory/services.py`, sin MAX+1, reinicio o reutilización; mapear duplicados concurrentes a 409 fuera del atomic fallido (FR-002, FR-007, FR-023).
- [X] T013 [US1] Implementar serializadores de entrada estricta/salida, POST /assets/, GET /assets/{id}/ mínimo, GET/POST /custodians/ y opciones fijas en `backend/inventory/serializers.py`, `backend/inventory/views.py`, `backend/inventory/urls.py`; campos reservados/extra rechazados, assignment/custodio inicial de servidor (FR-003–FR-007, FR-015, FR-019, FR-021).
- [X] T014 [US1] Implementar formularios de activo/custodio con etiquetas, tamaños y errores por campo en `frontend/src/components/Registration.tsx`; conectar alta a ficha mínima en `frontend/src/App.tsx`; asignación Disponible fija y código tras guardar (FR-001–FR-007, FR-015, FR-019, FR-021).

## Fase 4: US2 — entregar y devolver (P1)

Ciclo de custodia coherente y autores conservados. Prueba independiente: activo y custodio ficticios, entrega a destino, devolución a recepción y rechazo de estados incompatibles.

- [X] T015 [US2] Probar entrega/devolución, condición, ubicaciones, autor real obtenido del request, rechazo de campos reservados, CSRF de escrituras de movimientos, nota opcional y devoluciones sin entrega activa en `backend/inventory/tests/test_custody.py`; fallo al insertar evento debe revertir ficha en misma prueba (FR-011–FR-014, FR-020, FR-023; SC-006–SC-008, SC-012, SC-014).
- [X] T016 [US2] Crear Movement y migración en `backend/inventory/models.py`, `backend/inventory/migrations/0001_initial.py` y `backend/inventory/migrations/0002_integrity.py`: actor/asset «FK ... PROTECT», occurred_at automático, type «entrega, devolucion, cambio_condicion, rectificacion», before/after JSON de condition/assignment/custodian_id/location, actor_label y custodian_snapshot históricos, note/reason «texto, 2000», note opcional; rectifies «OneToOne Movement nullable, PROTECT» solo rectificación; resulting_revision única por activo. Impedir UPDATE/DELETE de originales mediante modelo y trigger PostgreSQL; no registrar admin editable (FR-014, FR-016, FR-022).
- [X] T017 [US2] Implementar entregar/devolver en `backend/inventory/services.py`: atomic, bloqueo de Asset sin join nullable, comparar expected_revision no negativa, verificar condición/custodia vigente, snapshot anterior/posterior, autor del request y revisión +1; error 409 sin cambios parciales (FR-012–FR-014, FR-020, FR-023).
- [X] T018 [US2] Exponer deliver/return y movements con serializadores estrictos en `backend/inventory/serializers.py`, `backend/inventory/views.py`, `backend/inventory/urls.py`; historiales orden id descendente y snapshots de custodio (FR-001, FR-012–FR-014, FR-020, FR-022).
- [X] T019 [US2] Implementar entrega/devolución y refresco de ficha/historial en `frontend/src/components/Movements.tsx`; presentar destino/recepción y condición, deshabilitar envío en curso y recargar ante revisión obsoleta sin reintento automático; probar en `frontend/src/tests/custody.test.tsx` (FR-001, FR-012–FR-014, FR-020, FR-023).

## Fase 5: US3 — rectificar el último movimiento (P2)

Original conservado y estado anterior restaurado. Prueba independiente: fixtures de entrega/devolución, rectificación y casos inelegibles sin depender de la pantalla de búsqueda.

- [X] T020 [US3] Probar rectificar entrega/devolución y restaurar condición/asignación/custodio/ubicación; motivo requerido, objetivo ajeno, repetido, rectificación de rectificación y A→B→rectifica B no habilita A en `backend/inventory/tests/test_rectification.py` (FR-016–FR-017, FR-020; SC-009, SC-014).
- [X] T021 [US3] Implementar elegibilidad sobre último evento incluidas rectificaciones, vínculo único y restauración del snapshot original con revisión +1 en `backend/inventory/services.py` (FR-016–FR-017, FR-020, FR-023).
- [X] T022 [US3] Exponer POST rectify, rectifiable_movement_id y vínculos rectifies_id/rectified_by_id sin actualizar original en `backend/inventory/serializers.py`, `backend/inventory/views.py`, `backend/inventory/urls.py` (FR-016–FR-017, FR-022).
- [X] T023 [US3] Añadir formulario con objetivo/efecto, motivo obligatorio y nota opcional en `frontend/src/components/Movements.tsx`; probar motivo, revisión y originales visibles en `frontend/src/tests/rectification.test.tsx` (FR-001, FR-016–FR-017).

## Fase 6: US4 — cambiar condición (P2)

Cambio real solo Disponible con motivo. Prueba independiente: Averiado→En reparación→Operativo, rechazo si Asignado/sin motivo/condición igual; rectificar último cambio restaura condición.

- [X] T024 [US4] Probar cambio real, motivo obligatorio, misma condición, Asignado, trazabilidad y rectificación del cambio en `backend/inventory/tests/test_condition.py` (FR-014, FR-016–FR-018; SC-009, SC-010).
- [X] T025 [US4] Implementar servicio de cambio con snapshot, motivo, actor y revisión, más contrato POST condition en `backend/inventory/services.py`, `backend/inventory/serializers.py`, `backend/inventory/views.py`, `backend/inventory/urls.py` (FR-018, FR-023).
- [X] T026 [US4] Añadir formulario de condición distinta y motivo obligatorio a `frontend/src/components/Movements.tsx`; probar disponibilidad y validaciones en `frontend/src/tests/condition.test.tsx` (FR-001, FR-018).

## Fase 7: US5 — listado y ficha completos (P2)

Ficha individual, histórico y acceso uniforme. Prueba independiente: fixtures conocidos, listado, ficha inexistente, lista vacía y permisos de dos gestores.

- [X] T027 [US5] Probar listado/ficha, página 50, orden id descendente, ficha inexistente, originales/historial y permisos iguales en `backend/inventory/tests/test_queries.py` (FR-008, FR-010–FR-011, FR-014, FR-022; SC-001, SC-005, SC-013, SC-016).
- [X] T028 [US5] Completar GET listado/ficha y paginación estricta, precargar relaciones evitando consultas por fila y exponer opciones/ubicaciones actuales en `backend/inventory/views.py` y `backend/inventory/serializers.py` (FR-008, FR-014, FR-020).
- [X] T029 [US5] Implementar lista/ficha completa e historial visible con vínculos de rectificación, estado vacío/carga/error y fecha America/Guayaquil en `frontend/src/components/Inventory.tsx`, `frontend/src/components/History.tsx`, `frontend/src/App.tsx`; probar en `frontend/src/tests/queries.test.tsx` (FR-001, FR-008, FR-014, FR-022).

## Fase 8: US6 — búsqueda y filtros (P3)

Buscar por campos aprobados y combinar AND de filtros. Prueba independiente: datos variados, búsquedas por custodio actual, combinaciones, ningún resultado y valores inválidos.

- [X] T030 [US6] Probar cada campo de búsqueda parcial sin mayúsculas, cada filtro y combinaciones AND, custodio anterior excluido, ubicación exacta y consultas inválidas en `backend/inventory/tests/test_search.py` (FR-009; SC-005).
- [X] T031 [US6] Implementar búsqueda OR entre code/name/brand/model/serial_number/custodio actual y AND con category/condition/assignment/location/custodian en `backend/inventory/views.py`; validar enum/ID/page según contrato (FR-009).
- [X] T032 [US6] Implementar filtros, búsqueda, limpiar criterios y reinicio/conservación de página en `frontend/src/components/Inventory.tsx`; probar resultados/errores y peticiones obsoletas canceladas en `frontend/src/tests/search.test.tsx` (FR-001, FR-009).

## Fase 9: validación transversal y entrega

Todas las historias funcionan juntas; cada tarea se marca solo con evidencia.

- [X] T033 Probar carreras de alta idéntica/códigos distintos, doble entrega/devolución/rectificación y revisión obsoleta mediante PostgreSQL TransactionTestCase con conexiones independientes y coordinación en `backend/inventory/tests/test_concurrency.py` (FR-002, FR-007, FR-023; SC-015).
- [X] T034 Ejecutar check, suite completa PostgreSQL aislada y makemigrations --check --dry-run; registrar entorno/comandos/conteos/resultados en `specs/002-registro-consulta-activos/validation.md`; no declarar éxito ante fallos (FR-001, FR-023).
- [X] T035 Ejecutar pruebas web y build reproducible, corregir errores de integración y registrar resultados en `specs/002-registro-consulta-activos/validation.md` (FR-001).
- [X] T036 Comprobar en navegador el recorrido quickstart con dos gestores y datos ficticios, permisos/CSRF, historial, conflictos y logout; registrar evidencia y límites en `specs/002-registro-consulta-activos/validation.md` (FR-001, FR-010, FR-022–FR-023).
- [X] T037 Actualizar ejecución/pruebas/secretos y limitaciones reales en `README.md`, `backend/README.md`, `frontend/README.md` y `specs/002-registro-consulta-activos/quickstart.md`; no atribuir ratificación/reproducción al grupo (FR-001, FR-010).
- [X] T038 Revisar diff, archivos ignorados, trazabilidad y estado real de tareas en `specs/002-registro-consulta-activos/tasks.md`; preparar cambios revisables sin integrar develop/main ni solicitar revisión a compañeros mediante mensajes no autorizados (FR-001).

## Dependencias y orden de ejecución

Preparación → fundamentos → US1 → US2 → US3 → US4 → US5 → US6 → validación transversal. US5/US6 pueden probarse con fixtures propios tras el modelo de US1; el orden secuencial evita editar simultáneamente views.py/serializers.py y componentes compartidos. US3 necesita eventos de US2 y US4 integra su operación con la rectificación de US3. La ficha mínima de US1 permite verificar el primer incremento antes de completar el listado de US5.

Dentro de cada historia: pruebas de contrato/reglas → modelos/migraciones → servicio → API → interfaz/integración → verificación. Antes de implementar se ejecuta speckit-analyze. No comenzar una operación dependiente si fallan sus fundamentos. No se marcan tests como ejecutados por haberlos escrito.

## Oportunidades de trabajo paralelo

No se asigna [P] a tareas agregadas que escriben archivos compartidos o dependen de pasos todavía incompletos. Tras sus prerrequisitos hay pares de trabajo separados posibles:

| Historia | Ejemplo posible sin conflicto de archivos |
|---|---|
| US1 | Pruebas backend test_assets.py y pruebas web registration.test.tsx. |
| US2 | Pruebas backend test_custody.py y pruebas web custody.test.tsx. |
| US3 | Pruebas backend test_rectification.py y pruebas web rectification.test.tsx. |
| US4 | Pruebas backend test_condition.py y pruebas web condition.test.tsx. |
| US5 | Pruebas backend test_queries.py y pruebas web queries.test.tsx. |
| US6 | Pruebas backend test_search.py y pruebas web search.test.tsx. |

Son posibilidades de organización del equipo, no autorización para delegar o contactar a otros integrantes. Se evita trabajo simultáneo sobre models.py, services.py, views.py, serializers.py, App.tsx y Movements.tsx.

## Estrategia incremental y comprobación independiente

Primer incremento demostrable: fundamentos + US1, con registro y lectura mínima de un activo desde API/web, sin afirmar que las restantes historias estén listas. Después añadir custodia, rectificación, cambio de condición y consultas completas. El alcance final sigue incluyendo todas las historias aprobadas, no se reduce al primer incremento.

Cada fase de historia describe arriba su prueba independiente. Para cerrar el incremento completo deben pasar las pruebas automatizadas y el recorrido de quickstart, registrando evidencia en validation.md. Constitución y revisión grupal conservan su estado real; no marcar como realizadas revisiones humanas inexistentes.

## Cobertura de requisitos

| Requisito | Tareas relacionadas |
|---|---|
| FR-001 | T001, T002, T003, T008, T014, T018, T019, T023, T026, T029, T032, T034, T035, T036, T037, T038 |
| FR-002 | T009, T011, T012, T014, T033 |
| FR-003 | T009, T011, T013, T014 |
| FR-004 | T009, T011, T013, T014 |
| FR-005 | T009, T011, T013, T014 |
| FR-006 | T009, T011, T013, T014 |
| FR-007 | T009, T011, T012, T013, T014, T033 |
| FR-008 | T027, T028, T029 |
| FR-009 | T030, T031, T032 |
| FR-010 | T001, T004, T005, T006, T007, T008, T027, T036, T037 |
| FR-011 | T015, T027 |
| FR-012 | T015, T017, T018, T019 |
| FR-013 | T015, T017, T018, T019 |
| FR-014 | T015, T016, T017, T018, T019, T024, T027, T028, T029 |
| FR-015 | T009, T011, T013, T014 |
| FR-016 | T016, T020, T021, T022, T023, T024 |
| FR-017 | T020, T021, T022, T023, T024 |
| FR-018 | T024, T025, T026 |
| FR-019 | T009, T010, T013, T014 |
| FR-020 | T015, T017, T018, T019, T020, T021, T028 |
| FR-021 | T009, T011, T013, T014 |
| FR-022 | T016, T018, T022, T027, T029, T036 |
| FR-023 | T007, T012, T015, T017, T019, T021, T025, T033, T034, T036 |
