# Validación del incremento 002

**Fecha de revisión y pruebas:** 1 de noviembre de 2026, America/Guayaquil. **Rama:** feature/registro-consulta-activos. **Base:** 2502facef7ad57109a98cfa787ccd214507ef9cb.
**Resultado:** comprobaciones técnicas aprobadas; 28 pruebas backend y 17 frontend correctas. Revisión humana e integración por PR pendientes. La constitución sigue como propuesta sin ratificación atribuida al equipo.

## Evidencia ejecutada

| Comprobación | Resultado |
|---|---|
| PostgreSQL aislado: python backend/tools/test_postgres.py inventory --verbosity 1 | 28 pruebas correctas; clúster temporal detenido y eliminado. |
| npm test -- --run en frontend | 17 pruebas correctas en siete archivos. |
| npm run build en frontend | TypeScript sin errores y build Vite correcto. |
| manage.py check | Sin incidencias. |
| manage.py makemigrations --check --dry-run | No changes detected. |
| python -m pip check | No broken requirements found. |
| manage.py migrate --noinput en la base local configurada | inventory.0001_initial e inventory.0002_integrity aplicadas correctamente; sin recrear la base. |
| Navegador real contra web/API/PostgreSQL aislados | Recorrido comprobado con dos gestores y datos ficticios. |
| git fetch origin y comparación de base | Base de la rama: 2502fac, coincidente con origin/develop al iniciar la revisión. No se fusionó ni se tomó como origen el PR #8. |

Entorno comprobado: Windows, Python 3.13.14, Django 5.2.18, DRF 3.16.1, PostgreSQL 17.11, Node 22.23.1 y npm 10.9.8. React/React DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.4 y Vitest 5.0.5 están fijados; package-lock.json conserva la resolución de dependencias.

Las suites se escribieron antes de conectar sus funcionalidades y se observaron fallos iniciales de acceso e imports de componentes todavía ausentes. Los resultados anteriores corresponden a la versión final, no a esos estados intermedios.

## Cobertura de aceptación y código comprobado

| Requisitos | Pruebas / evidencia |
|---|---|
| FR-001 | Suite API, pruebas web y recorrido real conjunto; contratos API/web implementados. |
| FR-002 | AssetTests.test_creation_code_fields_and_stability y ConcurrencyTests.test_duplicate_registration_and_unique_codes. |
| FR-003–FR-006 | AssetTests.test_required_lengths_choices_and_reserved_fields, test_only_six_categories_and_no_edit_delete; formulario registration.test.tsx. |
| FR-007 | AssetTests.test_duplicates_normalized_but_internal_characters_preserved, test_data_endpoints_require_manager_and_unicode_identity y carrera de altas. |
| FR-008 | QueryTests y navegador: lista, código estable, ficha propia, lista vacía y recurso inexistente en API. |
| FR-009 | SearchTests para cada campo/filtro y combinación; search.test.tsx y navegador con resultados/ningún resultado/limpiar. |
| FR-010–FR-011 | PermissionTests, protección de endpoints de datos y ManagerCommandTests; dos gestores en navegador con autores distintos. |
| FR-012–FR-013 | CustodyTests, doble entrega/devolución concurrente y recorrido real de entrega/devolución. |
| FR-014 | CustodyTests.test_cycle_authors_locations_and_history, History y queries.test.tsx; autores y custodio previo visibles. |
| FR-015 | Alta Disponible/sin custodio, campos de servidor no suplantables; pruebas API y registro real en navegador. |
| FR-016–FR-017 | RectificationTests: restaurar entrega/devolución, objetivo ajeno, motivo, duplicada, rectificación de rectificación y antecedente con sucesores; original inmutable también ante SQL UPDATE/DELETE. |
| FR-018 | ConditionTests, condition.test.tsx y navegador: Averiado→En reparación, motivo y rectificación del cambio. |
| FR-019 | Custodios con correo válido de otro dominio, unicidad normalizada y ausencia de cuenta; registro web y prueba de formulario. |
| FR-020 | CustodyTests y RectificationTests restauran ubicaciones y custodia; destino/recepción comprobados en navegador. |
| FR-021 | Formularios/serializadores de marca/modelo/ubicación como texto; no se creó administración de catálogos. |
| FR-022 | Historial con originales y vínculos conservados, trigger contra UPDATE/DELETE y ausencia de rutas de borrado; revisión visual. |
| FR-023 | TransactionTestCase con conexiones independientes: alta duplicada/códigos únicos, doble entrega/devolución/rectificación; rollback al fallar evento y revisión obsoleta. |

Los SC-001–SC-016 se vinculan a las historias y pruebas mediante la tabla de aceptación en spec.md y las tareas correspondientes. La relación documental cubre 23/23 FR y 16/16 SC; no equivale a una medición de cobertura de líneas ni a una certificación de seguridad.

## Recorrido real de navegador (20 de octubre de 2026)

1. Acceso como qa_gestor_a en el entorno efímero; lista inicialmente vacía.
2. Registro de persona ficticia con correo example.org y dependencia opcional, sin cuenta de acceso.
3. Alta de Portátil de laboratorio, código TI-000001, Operativo/Disponible, Laboratorio 1 y sin custodio.
4. Entrega a esa persona y Aula 2; ficha Asignado e historial con autor A.
5. Cierre de sesión; acceso como qa_gestor_b, consulta del activo y devolución como Averiado a Laboratorio 1; sin custodio actual y autores A/B conservados.
6. Ausencia de acción Entregar mientras está Averiado; cambio real a En reparación con motivo.
7. Rectificación del último cambio: vuelve a Averiado, conserva evento original y nuevo vínculo. No se ofrece rectificar un antecedente tras esa rectificación.
8. Dos vistas de la misma ficha: formulario antiguo preparado, cambio válido a Operativo en la segunda vista, intento desde la primera rechazado con «La ficha cambió». Se recarga y conserva exactamente cinco movimientos válidos, sin reintento automático.
9. Búsqueda lab-001 + categoría Portátil + Disponible; cambio de filtro a Asignado da cero resultados. Limpiar recupera el activo.
10. Cierre de sesión vuelve a acceso y limpia la vista privada. Se cerraron solo las dos pestañas propias y se detuvieron sus servidores/base temporales.

Se revisó escritorio y vista estrecha. Las capturas muestran exclusivamente datos ficticios y no contraseñas. Se conservan ahora como evidencia de la comprobación del 20 de octubre de 2026: [ficha de escritorio](../../docs/evidencias/002-registro-consulta-activos/ficha.png) e [historial rectificado](../../docs/evidencias/002-registro-consulta-activos/historial.png). La revisión de noviembre repite las pruebas automatizadas; no presenta aquellas capturas como una nueva sesión de navegador. Los gestores de QA existieron solo en la base temporal ya eliminada y no son cuentas disponibles para el uso real.

## Correcciones y decisiones de ejecución

- Revisión de noviembre: se reprodujo el HTTP 500 al enviar listas JSON al login. Se añadió una regresión con ocho variantes inválidas y se corrigió la validación del cuerpo antes de recorrer sus claves. Se exige HTTP 400 en JSON y no se inicia sesión en estos casos. No se cambió el alcance funcional.


- Analyze detectó que T005 dependía de modelos futuros para probar autoría. Steven aprobó trasladar ese contenido a T009/T015; se repitió el análisis sin bloqueos pendientes. La revisión fue de solo lectura y la corrección se ejecutó como paso separado aprobado.
- En Windows pg_ctl podía mantener handles de salida heredados: el runner captura sus logs en archivo para permitir avanzar. Solo se detuvo el clúster creado por la prueba que había quedado esperando; no el servidor de desarrollo.
- La primera base temporal usó locale C y falló una búsqueda con tilde. Se adoptó proveedor ICU/und para Unicode; la base existente Spanish_Ecuador.1252 no se recreó ni se alteraron sus credenciales.
- Se protegió el cliente frente a fallos de red y respuestas no JSON: no anuncia éxito ni reenvía una escritura incierta; indica consultar ficha e historial. Las cancelaciones se distinguen del fallo de conexión.
- El esquema quedó en 0001_initial (modelos) y 0002_integrity (secuencia/trigger); las tareas se ajustaron a los nombres reales sin cambiar las reglas de negocio.

## Límites y trabajo del equipo

- Validación local en Windows; comandos Linux documentados, sin afirmar ejecución en otra máquina o por otro integrante.
- Sin SLA, prueba de carga institucional, despliegue público, auditoría externa ni política institucional de conservación inventada. Historial sin borrado automático.
- Constitución sin ratificación y PR sin revisión humana todavía. El incremento se publica mediante commits en feature/registro-consulta-activos y un PR dirigido a develop. Steven se reserva la aceptación/fusión de su PR y el cierre del PR #8; no se fusiona develop/main automáticamente ni se atribuye revisión por pares ya realizada.
- Copilot y Codex se conservan por decisión explícita; la advertencia de coexistencia de Spec Kit documentada en el registro de decisiones no se ocultó ni se resolvió cambiando herramientas sin autorización.
- Participación de IA: Codex asistió en diseño, código, pruebas y documentación; Steven definió las reglas mediante las aclaraciones. El equipo debe revisar el resultado y registrar sus contribuciones reales.

## Estado de tareas

38/38 tareas técnicas completadas con las comprobaciones y límites de este informe; el cierre no supone ratificación grupal, revisión por pares ni fusión de ramas. Las comprobaciones y marcas de checklist representan calidad de requisitos; no sustituyen la revisión humana del equipo.
