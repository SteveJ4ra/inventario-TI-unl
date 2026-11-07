# Validación 003 — evidencia final vigente

Fecha de consolidación: 2026-11-04 (America/Guayaquil). Resultados de la última ejecución funcional anterior a la interrupción, conservados en el historial de herramientas de esta sesión. No son resultados nuevos inferidos ni copiados de 002.

| Comprobación | Resultado real |
|---|---|
| Backend completo, PostgreSQL temporal | 182/182 PASS; 15.797 s |
| Frontend completo | 12 archivos, 57/57 PASS; 32.60 s |
| TypeScript/Vite | PASS; 31 módulos |
| manage.py check mediante runner aislado | Sin incidencias |
| makemigrations --check --dry-run mediante runner aislado | No changes detected |
| pip check | No broken requirements found |
| git diff --check | Sin errores; avisos de normalización LF/CRLF |

## Comandos efectivamente ejecutados

Desde raíz:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 0
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --manage check
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --manage makemigrations --check --dry-run
& ./backend/.venv/Scripts/python.exe -m pip check
git diff --check
~~~

Desde frontend:

~~~powershell
npm test -- --run
npm run build
~~~

El runner crea un clúster PostgreSQL privado con credenciales efímeras; no usa la base local ni modifica .env. Su modo --manage permite únicamente check y makemigrations --check --dry-run, no migrate.

## Cobertura y proveedores

- La suite completa incluye test_acquisition_schema y test_legacy_preflight: expansión vacía/histórica, constraints NOT VALID, preservación y protección SQL; plantilla de contracción probada fuera del grafo activo. El grafo Django sigue en 0004.
- test_document_edit: metadatos/revisiones completas, pertenencia, documento vacío, campos reservados, autorización/CSRF, SQL rollback y carreras de edición/asociación.
- test_import_acquisitions: gateway DjangoProviderGateway de producción explícito, compra compartida, donación con documento existente, revalidación real, rollback SQL, idempotencia concurrente y bloqueo explícito de donación CSV nueva. No se usó FakeGateway para afirmar estos resultados.
- test_metadata_edit y regresión previa: auditorías, snapshots, correos/identidades duplicados, revisiones/perfiles obsoletos, permisos e inmutabilidad; operaciones de custodia/condición/rectificación conservadas.
- React usa fetch simulado solo en tests, con cliente CSRF/PATCH real. Incluye edición documental y navegación con permisos explícitos.
- Proveedor real 005: NO INTEGRADO. Escenarios con guardia sustituida validan únicamente el servicio aislado.
- Creación de donación nueva CSV y proveedor de licencias 006: no se declaran integrados.
- Recorrido manual de navegador y migración local: NO EJECUTADOS.

## Continuidad tras la interrupción

La consolidación modificó únicamente documentación. Se inspeccionaron 94 archivos funcionales de backend/inventory, backend/config, backend/tools y frontend/src; ninguno fue modificado después del inicio de la validación final registrada. No se repitieron suites porque no hubo cambios funcionales. Se verificaron nuevamente rama, estado Git y formato documental. No se afirma una huella criptográfica capturada durante las pruebas anteriores.

## Fallos de desarrollo corregidos

El proveedor import_assets ausente produjo 503 y un AttributeError en fase roja; después se corrigió la normalización de campos no aplicables de compra. El PATCH documental inicialmente devolvía pending_decision; sus pruebas pasaron con el contrato humano confirmado. El formulario documental inicialmente no existía (fallo de resolución de módulo, no pruebas ejecutadas). La plantilla de contracción detectó eventos FK diferidos de fixtures antes de ALTER TABLE: se verificaron las FK con SET CONSTRAINTS ALL IMMEDIATE, sin desactivar integridad.

No se eliminaron pruebas ni se debilitaron contratos para obtener la suite verde. Los registros de bloques anteriores se conservan abajo como evidencia histórica, no como estado actual.


<details>
<summary>Historial de bloques anteriores — sus estados no sustituyen el cierre vigente</summary>

# Validación parcial 003 — 2026-11-04 (America/Guayaquil)

Los apartados iniciales conservan resultados históricos reales. Los resultados de expansión están en «Expansión T004» y el estado vigente en «T008–T010: compra compartida e interfaz» al final; no interpretar los bloqueos de esquema anteriores como actuales del entorno temporal. La base local nunca se migró.

Windows, PowerShell 7.6.9, Python 3.13.17, Node 24.18.0; dependencias fijadas Django 5.2.18/DRF 3.16.1. PostgreSQL 17 del runner aislado. Ningún comando migrate se ejecutó contra la DB local. El runner aplica solo las migraciones existentes a su clúster temporal privado y lo elimina al terminar. No se leyó .env para exponer credenciales.

## Ejecución real del bloque inicial (resultados históricos de esta sesión)

1. PASS: git branch --show-current devuelve Alex_Sigcho_Feature; git status --short inicial sin salida.
2. PASS: con SPECIFY_FEATURE_DIRECTORY=specs/003-fichas-adquisiciones y SPECIFY_FEATURE_NO_PERSIST=1, ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks devuelve 003 y sus documentos. El primer intento sin variables falló sin modificar el marcador; se corrigió la selección explícitamente.
3. PASS inicial: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py — 45/45. Evidencia base real, no conteo copiado.
4. FAIL esperado de fase roja inicial: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions inventory.tests.test_permissions --verbosity 1 — 16 tests, failures=9, errors=1. Rutas ausentes 404, PATCH 405, sesión Operador 403, comando y modelos ausentes. Incluía cinco pruebas históricas PermissionTests.
5. PASS tras modelos: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models inventory.tests.test_assets inventory.tests.test_condition inventory.tests.test_custody inventory.tests.test_imports inventory.tests.test_management inventory.tests.test_permissions.PermissionTests inventory.tests.test_queries inventory.tests.test_rectification inventory.tests.test_search inventory.tests.test_concurrency --verbosity 1 — 50/50.
6. FAIL esperado de fase roja final: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions inventory.tests.test_permissions.OperatorContractTests --verbosity 1 — 14 tests; failures=15 (incluye subtests), errors=1. No se usa expectedFailure ni skip para ocultarlos. Un caso de denegación a Operador ya pasa por la protección Gestor existente. Error de servicio: UndefinedTable inventory_faculty, dependencia de T004; no se confunde con prueba ejecutada del rollback. Los demás fallos son funcionalidad T005–T007 pendiente, no regresiones demostradas de 002.
7. PASS: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models --verbosity 1 — 5/5 tras aquel cambio del modelo.
8. PASS final tras guarda 008: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models inventory.tests.test_acquisition_gateway inventory.tests.test_assets inventory.tests.test_condition inventory.tests.test_custody inventory.tests.test_imports inventory.tests.test_management inventory.tests.test_permissions.PermissionTests inventory.tests.test_queries inventory.tests.test_rectification inventory.tests.test_search inventory.tests.test_concurrency --verbosity 1 — 51/51, 3.043 s; checks Django sin incidencias.
9. PASS: npm.cmd --prefix frontend test -- --run — 20/20, 8 archivos. PASS: npm.cmd --prefix frontend run build — TypeScript/Vite correctos.
10. PASS: & ./backend/.venv/Scripts/python.exe -m pip check — No broken requirements found. PASS: & ./backend/.venv/Scripts/python.exe backend/manage.py check — sin incidencias.
11. FAIL esperado/pendiente T004: & ./backend/.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run --noinput — salida 1; propone 0004 con siete modelos y constraints. No escribió archivo ni aplicó migración. Este chequeo no acredita un esquema sincronizado.
12. PASS: git diff --check — sin errores de whitespace; avisos de normalización LF/CRLF de Git.

## Alcance de la evidencia

FR-001: regresión base verde. FR-002/004/007–012/016: aceptación nueva todavía roja. FR-005/007–012/015: validación parcial del modelo y la frontera 008, no integridad SQL desplegada. FR-003/013: preservación real al editar custodio NO EJECUTADA porque T014 no existe. Revisión global, documentos auditados compartidos y concurrencia nueva: NO EJECUTADOS. Migración histórica y esquema 003: NO IMPLEMENTADOS/NO APLICADOS. 005: DEPENDENCIA NO INTEGRADA. 008: pruebas existentes usan FakeGateway; la nueva prueba simula solo introspección faltante. No se probó importación con proveedores 003/006 reales.

La suite completa incluye pruebas deliberadamente rojas: no se declara PASS global de 003 ni preparación para despliegue. No hubo validación manual en navegador ni revisión humana del código. Constitución sigue propuesta.


## Correcciones técnicas posteriores a la auditoría — 2026-11-04

Esta sección describe el estado actual; los conteos 45/50/51 anteriores son ejecuciones históricas reales, no el resultado vigente de todos los tests. No se ejecutó makemigrations, ni siquiera dry-run, en este bloque de correcciones. Se verificaron rama y estado previo conservado; prerrequisitos 003 y checklist 10/10; no hay extensions.yml.

### Secuencia de pruebas focalizadas real

- & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models --verbosity 1: primero 9 métodos, failures=16 por subtests, confirmando falta de constraints/guardas; después de corregir modelos 9/9 PASS. Algunas operaciones rojas intentaban acceder a DB desde SimpleTestCase, demostrando que faltaba el rechazo previo, no un rechazo SQL de integridad.
- & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_gateway --verbosity 1: 7 métodos, failures=1/errors=1 antes de la corrección. Se detectó dependencia interna ocultada como ProviderUnavailable y función no invocable aceptada. Un intento posterior combinado de 16 métodos repitió estos mismos dos problemas porque la sustitución de texto no había coincidido con los finales CRLF; se corrigió la edición y se verificó el archivo real.
- & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models inventory.tests.test_acquisition_gateway --verbosity 1: 19/19 PASS tras esas correcciones y nuevos casos positivos/guardas. Luego se añadió un caso de textos obligatorios de 002.

### Regresión final seleccionada: PASS

Comando exacto:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models inventory.tests.test_acquisition_gateway inventory.tests.test_assets inventory.tests.test_condition inventory.tests.test_custody inventory.tests.test_imports inventory.tests.test_management inventory.tests.test_permissions.PermissionTests inventory.tests.test_queries inventory.tests.test_rectification inventory.tests.test_search inventory.tests.test_concurrency --verbosity 1
~~~

Resultado final: 65/65 en 2.426 s, salida 0, checks sin incidencias. Incluye las 45 pruebas existentes y 20 de modelos/frontera. Una ejecución anterior a añadir el último caso pasó 64/64. No se presenta como suite completa verde: excluye explícitamente la aceptación aún no implementada.

### Aceptación pendiente: FAIL/BLOQUEADA, sin ocultar

Comando: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions inventory.tests.test_permissions.OperatorContractTests --verbosity 1

Resultado: 14 métodos, failures=17 contando subtests, errors=0, salida 1. Sin skip ni expectedFailure.

| Clasificación | Métodos | Evidencia |
|---|---:|---|
| BLOQUEO_ESQUEMA_T004 | 4 | Edición general, servicio de rollback, Gestor que intenta cambiar facultad y Operador que intenta editar ficha; faltan tablas de adquisición/facultad. No alcanzan las operaciones objetivo. |
| FUNCIONALIDAD PENDIENTE | 10 | 5 métodos API de adquisición con 404 (incluye validación de compra con cuatro subtests); 5 de Operador por rutas 404, login 403 y comando ausente. |
| Error inesperado de ejecución | 0 | Ya no aparece UndefinedTable; hay diagnóstico explícito previo. Esto no acredita ausencia de defectos latentes tras completar T004–T007. |

Se corrigió el defecto de fixture antigua y los ids inexistentes. Se eliminó el orden de respuesta impuesto. La comprobación posterior de ficha/auditoría solo se acreditará cuando exista esquema: no se declara probada por haber alcanzado el bloqueo previo. La función de fixture usa datos ficticios y código de prueba explícito; no modifica generador productivo ni inventa legado.

### Comprobaciones adicionales repetidas

- npm.cmd --prefix frontend test -- --run: PASS, 20/20 en 8 archivos.
- npm.cmd --prefix frontend run build: PASS TypeScript/Vite.
- & ./backend/.venv/Scripts/python.exe -m pip check: PASS, No broken requirements found.
- & ./backend/.venv/Scripts/python.exe backend/manage.py check: PASS sin incidencias.
- git diff --check: PASS sin errores; avisos LF/CRLF de Git.
- Get-ChildItem backend/inventory/migrations -Filter '*.py': solo __init__, 0001, 0002 y 0003. No se generó ni aplicó una migración nueva.

### Límites que sustituyen interpretaciones demasiado amplias

La prueba de moneda evalúa defaults de objetos sin guardar, no persistencia histórica. Los CHECK se evalúan con SELECT PostgreSQL contra expresiones de valores; no se crearon tablas 003 ni se probó un INSERT directo contra constraints instalados. Unicidad de revisiones declarada pero no ejecutada contra DB. Guardas ORM verificadas; triggers nuevos no implementados. Los tests de gateway simulan introspección/importación y excepciones, no proveedores reales. Los tests existentes de CSV usan FakeGateway. FR-003/013 (edición y snapshots), revisión global, concurrencia documental, import_assets y 005 siguen NO EJECUTADOS/DEPENDENCIA NO INTEGRADA.


## Expansión T004 — resultado vigente del bloque autorizado

### Generación y entorno

Se generó únicamente backend/inventory/migrations/0004_acquisition_expansion.py mediante un script offline ejecutado por & ./backend/.venv/Scripts/python.exe - (here-string de PowerShell). Usó MigrationLoader(None), MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps), NonInteractiveMigrationQuestioner()).changes(graph=loader.graph, migration_name='acquisition_expansion') y MigrationWriter. Se proporcionaron variables de entorno ficticias para settings sin abrir conexión; el loader confirmó la hoja 0003_importbatch. Después se editaron nueve CHECK a NOT VALID y se añadió el RunSQL de conservación irreversible. No se ejecutó manage.py migrate contra PostgreSQL local ni se modificó .env.

Las pruebas siguientes arrancan exclusivamente el clúster temporal privado de backend/tools/test_postgres.py. La prueba histórica crea un schema con prefijo test_003_ y UUID, cambia search_path temporalmente, migra 0003→0004 y restaura search_path; sus cambios se revierten por la transacción del TestCase, sin tocar datos externos. Los datos históricos son fixtures explícitas, no datos extraídos del usuario.

### Pruebas focalizadas

Comando repetido: & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_schema --verbosity 1

- Primera ejecución antes de añadir los triggers/NOT VALID: 6 métodos, failures=5 y errors=1. Los UPDATE/DELETE todavía se permitían y el CHECK convencional impedía expandir una fila histórica ficticia con nombre blanco. Esa versión intermedia no se entrega como correcta.
- Tras implementar triggers/NOT VALID: 6/6 PASS.
- Al ampliar cobertura a diez casos: 1 fallo de la prueba que comparaba el estado de todas las apps, incluidas apps Django ajenas al paquete; se corrigió para trim_to_apps={'inventory'}, sin alterar código de terceros.
- Última ejecución focalizada: 10/10 PASS, 1.385 s.

Cobertura real: migración inicial de base vacía; Asset.faculty nullable sin default DB/ORM; alta antigua de 002 sin facultad; coincidencia del estado de inventory con modelos; reversión rechazada con IrreversibleError sin retirar 0004; nueve CHECK de legado no validados; constraints nuevos y unicidad instalada; UPDATE/DELETE SQL rechazados en cuatro auditorías con SQLSTATE 55000; DELETE de dominio sin referencias/multifila sin efectos parciales; FK de facultad y una línea por activo; textos/fecha desconocida y revisión positiva/única; migración desde 0003 con conservación exacta de activo, Movement e ImportBatch, texto histórico defectuoso intacto y cero facultades/documentos/líneas/auditorías inventados.

### Regresión seleccionada — PASS

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_schema inventory.tests.test_acquisition_models inventory.tests.test_acquisition_gateway inventory.tests.test_assets inventory.tests.test_condition inventory.tests.test_custody inventory.tests.test_imports inventory.tests.test_management inventory.tests.test_permissions.PermissionTests inventory.tests.test_queries inventory.tests.test_rectification inventory.tests.test_search inventory.tests.test_concurrency --verbosity 1
~~~

75/75, 4.198 s, salida 0: 45 existentes + 20 modelos/frontera + 10 expansión. Checks Django sin incidencias. No representa una suite completa verde de 003.

### Aceptación nueva — FAIL por implementación pendiente

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions inventory.tests.test_permissions.OperatorContractTests --verbosity 1
~~~

14 métodos, failures=15 contando subtests, errors=1, salida 1. Ya no hay bloqueo por tablas ausentes. Rutas de adquisición/facultades devuelven 404, PATCH de activo 405, login Operador 403 y create_operator no existe. El error de servicio es TypeError: Asset() got unexpected keyword arguments: 'acquisition_document_id', 'item_value', 'acquired_on', porque create_asset todavía implementa solo 002 y T006 no separa esos datos para crear la línea. El rollback de adquisición aún no se alcanza ni se acredita. El caso de Operador sin permiso de edición pasa por la protección Gestor existente, no demuestra que la nueva operación esté implementada.

### Otras comprobaciones repetidas

- npm.cmd --prefix frontend test -- --run: PASS, 20/20, ocho archivos.
- npm.cmd --prefix frontend run build: PASS TypeScript/Vite.
- git diff --check: PASS; solo avisos de normalización LF/CRLF.
- Inventario de migraciones: __init__, 0001_initial, 0002_integrity, 0003_importbatch y nueva 0004_acquisition_expansion. Ninguna migración previa modificada.

### Límites pendientes

No se aplicó nada local; tampoco se verificó de nuevo el conteo local 0 informado por Alex. Falta completar/validar legado, validar los CHECK NOT VALID y exigir faculty NOT NULL tras adaptar altas. TRUNCATE/DROP/desactivación de triggers por roles privilegiados no se impiden con los triggers de fila entregados; revisión de privilegios pendiente. Los servicios, auditoría global entre tablas, snapshots al editar custodios, concurrencia compartida, 005 e import_assets real siguen pendientes. No se resolvieron decisiones monetarias, de fecha de donación, cambio de origen o adaptación CSV por inferencia.


## Inicio T005/T006 — resultado vigente del bloque autorizado

Todo acceso de pruebas a PostgreSQL se realizó mediante backend/tools/test_postgres.py. No se ejecutaron comandos Django contra la DB local, no se modificó .env ni se generó una migración. Rama verificada Alex_Sigcho_Feature, cambios previos conservados. Checklist 10/10 y sin extensions.yml/hooks.

### Comprobación previa T004

& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_schema --verbosity 1

PASS 10/10, 2.161 s antes de programar. Se revisaron dependencia de 0003_importbatch, relaciones, nulabilidad, NOT VALID, SQL de conservación y prueba de historia 0003→0004. No se detectó un problema estructural que requiriera cambiar la migración. TRUNCATE/DROP privilegiados siguen fuera de la protección de fila, ya documentado.

### Servicios nuevos: evolución de pruebas real

- & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_domain --verbosity 1: fase roja inicial con error de descubrimiento, porque acquisition_services todavía no existía. Ningún caso funcional se ejecutó en ese intento.
- & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_domain inventory.tests.test_acquisitions.AcquisitionServiceTests --verbosity 1: primera implementación 10/10; cobertura ampliada 16/16; última ejecución focalizada 17/17 en 1.375 s.
- En la versión final las dos pruebas de fallo tras INSERT provocan UNIQUE real en PostgreSQL mediante una segunda inserción de la misma línea/revisión; se usa mock solo para inyectar ese punto de fallo, no una DB simulada. Se comprueba rollback de activo/línea o de edición/auditoría. No se debilitaron assertions, constraints ni se añadieron skips.

### Selección final de regresión — PASS

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_domain inventory.tests.test_acquisitions.AcquisitionServiceTests inventory.tests.test_acquisition_schema inventory.tests.test_acquisition_models inventory.tests.test_acquisition_gateway inventory.tests.test_assets inventory.tests.test_condition inventory.tests.test_custody inventory.tests.test_imports inventory.tests.test_management inventory.tests.test_permissions.PermissionTests inventory.tests.test_queries inventory.tests.test_rectification inventory.tests.test_search inventory.tests.test_concurrency --verbosity 1
~~~

92/92 en 6.999 s, salida 0, checks Django sin incidencias. Desglose: 45 existentes + 20 modelos/frontera + 10 expansión + 16 pruebas nuevas de servicios + 1 prueba de servicio T001 anteriormente roja. Incluye carreras reales con ThreadPoolExecutor y conexiones independientes; una edición/alta confirma y la otra devuelve conflicto, sin dobles líneas/auditorías.

Cobertura nueva: documento de metadatos sin activos; compra/donación básica compartida por altas; fecha/motivo exclusivo; reservados y referencias inexistentes sin escrituras; precisión decimal/NaN/Infinity; duplicidad en alta y edición; autorización Gestor separada de Operador; auditoría con actor/revisión y snapshots monetarios; preservación de snapshot de custodio en Movement al editar metadatos del activo; revisión obsoleta; rectificación antigua rechazada también por la ayuda de presentación. import_assets real, edición documental compartida y edición del perfil de custodio no se probaron porque no se implementaron.

### Aceptación API/Operador pendiente — FAIL

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions.AcquisitionApiTests inventory.tests.test_permissions.OperatorContractTests --verbosity 1
~~~

13 métodos, failures=15 contando subtests, errors=0, salida 1. Las rutas de adquisición/facultades no existen (404), PATCH de activo no está expuesto (405), login Operador todavía devuelve 403 y create_operator está ausente. Es T007 fuera del alcance autorizado. Un rechazo a Operador pasa por la protección Gestor anterior; no prueba un nuevo endpoint. La prueba de servicio separada ahora pasa y el TypeError de argumentos acquisition_document_id/item_value/acquired_on quedó resuelto; no se eliminó su aserción de rollback ante duplicado.

### Comprobaciones adicionales

- npm.cmd --prefix frontend test -- --run: PASS 20/20, ocho archivos.
- npm.cmd --prefix frontend run build: PASS TypeScript/Vite.
- git diff --check: PASS sin errores; avisos LF/CRLF.
- El estado de migración de inventory frente a modelos se verifica dentro de test_acquisition_schema, con PostgreSQL temporal; no fue necesario conectar localmente para un dry-run.

### Límites funcionales vigentes

T005/T006 parciales. Los serializadores validan estructura/condiciones aprobadas, pero no deciden signo/cero ni fecha documental de donación. Antes de escribir, los servicios informan pending_decision para importes <= 0 y fecha documental explícita de donación: es una parte no implementada, no aprobación de una prohibición de negocio. Se probó la ausencia de escrituras en esos casos. Sin constraints nuevos de dinero, cambios de origen con líneas, reasignación de documento ni edición documental compartida. La primitiva update_asset cubre fundamentos de T006, sin implementar el PATCH/flujo T014 o la edición de perfil de custodio. 008 conserva sus pruebas con FakeGateway, pero no hay adaptador import_assets ni equivalencia aprobada support_description/support_type. T004 sigue sin completado de legado/NOT NULL y no se aplicó localmente. No se declara suite global de 003 aprobada.


## T007: sesión, permisos y API — estado vigente 2026-11-04

Rama Alex_Sigcho_Feature verificada; prerrequisitos 003, checklist 10/10 y sin hooks. Cambios anteriores conservados. Solo PostgreSQL temporal de backend/tools/test_postgres.py; no migración ni creación de usuarios/datos locales, no .env, commits, push ni PR.

### Ejecuciones reales de este bloque

1. & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_operator_api --verbosity 1 — fase roja inicial: 8 métodos, failures=5/errors=2. Faltaban permissions en sesión, rutas y comando; un caso de rechazo ya pasaba. Ningún resultado de esa ejecución se declaró aprobado.
2. & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_operator_api inventory.tests.test_acquisitions inventory.tests.test_permissions --verbosity 1 — tras conectar servicios/sesión/rutas, 27/27 PASS.
3. & ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 1 — primera suite completa: 113 métodos, 1 fallo. La petición CSRF válida de test_assets seguía enviando el cuerpo de alta antiguo sin adquisición. Se corrigió su fixture, sin cambiar los estados esperados 403 sin token/201 con token ni relajar validación. Se añadieron cinco casos de cobertura de T007.
4. Mismo comando completo — resultado final: 118/118 PASS, 8.513 s, salida 0; checks Django sin incidencias. No es una selección recortada: incluye 002/008, expansión, servicios y toda la aceptación actualmente escrita.
5. npm.cmd --prefix frontend test -- --run — PASS 20/20, ocho archivos.
6. npm.cmd --prefix frontend run build — PASS TypeScript/Vite. No se probó recorrido manual de UI 003; aún falta implementarlo en sus tareas.
7. git diff --check — PASS, avisos LF/CRLF. Revisión de sintaxis de archivos modificados/nuevos sin acceso a DB local. No migraciones nuevas en este bloque.

### Métodos de aceptación: comparación nominal rojo → verde

Comando de comprobación explícita:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions.AcquisitionApiTests inventory.tests.test_permissions.OperatorContractTests --verbosity 2
~~~

13/13 PASS, 0.380 s. Los 15 fallos anteriores contaban subtests; correspondían a doce métodos fallidos y uno que ya pasaba.

| Método | Antes de T007 | Ahora |
|---|---|---|
| AcquisitionApiTests.test_donation_metadata_without_invoice | FAIL 404 | PASS |
| AcquisitionApiTests.test_general_edit_requires_reason_and_rejects_reserved_state | FAIL 405 | PASS |
| AcquisitionApiTests.test_metadata_document_without_assets_and_shared_purchase | FAIL 404 | PASS |
| AcquisitionApiTests.test_purchase_required_fields_and_no_partial_document | FAIL 404 (4 subtests) | PASS |
| AcquisitionApiTests.test_shared_donation_retains_individual_estimates | FAIL 404 | PASS |
| AcquisitionApiTests.test_unknown_acquisition_date_requires_reason_and_rejects_both | FAIL 404 | PASS |
| OperatorContractTests.test_anonymous_and_inactive_operator_denied | FAIL 404 | PASS |
| OperatorContractTests.test_faculty_administration_requires_operator_and_csrf | FAIL 404 | PASS |
| OperatorContractTests.test_local_provision_creates_only_operator | FAIL comando ausente | PASS |
| OperatorContractTests.test_manager_cannot_administer_faculties_or_change_asset_faculty | FAIL 404 | PASS |
| OperatorContractTests.test_operator_login_me_logout_without_inventory_access | FAIL login 403 | PASS |
| OperatorContractTests.test_provision_password_mismatch_leaves_no_account | FAIL comando ausente | PASS |
| OperatorContractTests.test_operator_cannot_edit_asset_description | PASS por guarda Gestor anterior | PASS, ahora con endpoint PATCH real |

Ninguno de esos métodos sigue fallando. No se eliminaron tests para obtener ese resultado. Las fixtures API de InventoryCase/test_assets incorporan facultad/documento reales ficticios creados bajo demanda; los helpers de legado de servicios permanecen. La antigua expectativa de PATCH siempre 405 se actualizó al contrato aprobado de 003: PUT/DELETE siguen 405 y PATCH vacío exige reason/revisión con 400 y sin cambio de estado.

### Cobertura nueva de T007

13 métodos en test_operator_api: permisos de sesión exactos, login/logout/CSRF, ausencia de permiso Gestor implícito, superusuario sin grupo/inactivo/anónimo denegados, sesión previa eliminada en login rechazado, provisión con usuario existente/contraseña débil, catálogo único normalizado y PATCH sin reactivar por default, referencia conservada al renombrar/desactivar, creación/lectura de documento, alta completa obligatoria, edición auditada/historia combinada, revisión obsoleta sin escrituras y rechazos de campos reservados. Operador sigue sin acceso a endpoints ordinarios/importación.

Se comprobaron explícitamente respuestas sin éxito ficticio: cambio de facultad 503 por 005 ausente sin cambiar revisión/facultad/auditoría; PATCH documental 409 pending_decision sin alterar referencia; PATCH custodio 503 sin alterar perfil ni crear auditoría; items iniciales no vacíos 503 sin crear documento; importes/fecha de donación no aprobados 409 sin escrituras. El bloqueo no constituye ejecución exitosa de esas funcionalidades.

### Límites y revisión pendiente

T001–T007 conservan estado parcial. La suite actual está verde, pero faltan casos/implementación de cambio de facultad con proveedor 005 real, edición documental y concurrencia compartida completa, edición auditada de custodio y orquestación de líneas iniciales. import_assets sigue ausente; las pruebas 008 usan su FakeGateway y no acreditan proveedor de importación 003 real. Cero/negativos, adaptación support_description, fecha documental de donación y cambio de origen siguen sin decisión nueva. Frontend todavía no recoge los nuevos campos obligatorios del alta ni ofrece administración Operador; test/build no son validación manual de ese flujo. T004 no está aplicada localmente ni completa por mapeo/VALIDATE/NOT NULL.


## T008–T010: compra compartida e interfaz — estado vigente 2026-11-04

Rama Alex_Sigcho_Feature verificada, cambios anteriores conservados. Prerrequisitos con selección explícita/no persistente devuelven 003; checklist 10/10, sin extensions.yml/hooks. No migraciones nuevas ni aplicación local, no .env/datos locales, commits, push o PR. No se instalaron dependencias ni se alteraron lockfiles.

### Nuevas pruebas backend de compra

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions.PurchaseFlowTests --verbosity 1
~~~

Seis métodos. Primera ejecución: cinco pasaron y uno dio KeyError por asset_code aún ausente en la salida de línea. Se añadió ese campo readonly y lectura autorizada con prefetch; segunda ejecución 6/6 PASS en 0.177 s. No se quitó la comprobación.

Casos reales con API Django y PostgreSQL temporal: una compra, dos activos con importes exactos asociados por id (sin imponer orden), total común único y sin invoice_total por línea, errores de entrada sin activo/línea parcial, violación UNIQUE real después de INSERT y rollback de ambas filas, fallo de una segunda alta que conserva la primera/factura, GET sin cambios de revisión ni auditoría. Los datos son fixtures, nunca históricos locales. El mock se usa únicamente para disparar una segunda inserción real conflictiva, no para simular una DB que aprueba.

### Nuevas pruebas frontend y correcciones de prueba

~~~powershell
npm.cmd --prefix frontend test -- --run src/tests/acquisition.test.tsx
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
~~~

- Fase roja inicial: suite no cargó porque AcquisitionForm todavía no existía; cero casos ejecutados en ese intento.
- Primera implementación: 5/5 pruebas nuevas PASS; build falló por opción exact no admitida por getByRole en la prueba. Se corrigió la consulta de prueba sin modificar reglas del producto.
- Regresión ampliada: 29/29 y build PASS.
- Al añadir integración completa de App: 32/33 PASS; un fallo por consulta ambigua Ubicación (registro y filtro). Se acotó la consulta con within al formulario de registro, manteniendo todas las aserciones. Después 33/33 PASS y build PASS.
- Se añadió el caso de segundo activo rechazado con primero ya confirmado. Última ejecución completa: 34/34 PASS, nueve archivos, 23.79 s; build TypeScript/Vite PASS.

Las 14 pruebas nuevas usan fetch simulado y el cliente HTTP real, incluidas credenciales same-origin y CSRF. Cubren factura primero y dos activos con valores distintos/fecha desconocida, campos obligatorios, errores por campo sin éxito, factura existente sin POST adicional, navegación y lock de envío conservados (también al cerrar mientras se guarda), rechazo de Operador sin permiso Gestor, JSON incompleto y error de red sin reintento automático, no tratar donación como compra, catálogo vacío sin facultad ficticia, ficha integrada de App y fallo de segundo activo conservando el primero. No son pruebas de navegador contra un servidor real; se complementan con la API/DB real anterior.

### Regresión backend completa final

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 1
~~~

124/124 PASS en 7.329 s, salida 0, checks Django sin incidencias: los 118 anteriores más seis nuevos. Incluye 002, importación 008 existente, provisión/sesión/permisos/CSRF, esquema, servicios y carreras de revisiones de los bloques previos. No se cambiaron pruebas anteriores para omitir un fallo.

### Límites del resultado

Ninguna prueba ejecutada queda fallando al final. No se probó manualmente un navegador con backend local ni se aplicaron migraciones locales. La UI confirma solo respuestas de éxito válidas; mantiene factura/datos ante rechazo y no reenvía automáticamente. La atomicidad es por activo+línea: la factura creada antes y activos anteriores exitosos permanecen si falla otro. No se promete rollback de toda la compra ni idempotencia de POST documental tras reintentos manuales con respuesta perdida.

POST documental con items iniciales de activos existentes sigue 503 y sin prueba positiva integral; no se inventaron fecha/revisión/motivo ni se omitieron guardas del servicio associate_asset. Por ese cierre pendiente se conservan T008–T010 parciales, aunque el formulario y las pruebas del flujo factura-primero para activos nuevos están implementados. No se cierra por inferencia T001–T007, 005/008 real, edición documental/custodio, mapeo/VALIDATE/NOT NULL ni políticas funcionales pendientes. No se avanzó a T011–T018.

## Validación final: asociaciones iniciales de compra — 2026-11-04

Comandos ejecutados desde raíz, salvo npm desde frontend:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions.PurchaseExistingItemsTests inventory.tests.test_acquisition_domain --verbosity 0
# 26/26 PASS, 1.945 s
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 0
# 134/134 PASS, 8.955 s; system check sin incidencias
npm test -- --run
# final: 9 archivos, 37/37 PASS, duración 29.90 s
npm run build
# TypeScript + Vite PASS, 26 módulos
git diff --check
# exit 0; avisos de normalización LF/CRLF, sin errores de whitespace
~~~

Incidencias reales: primera ejecución frontend 35/37 por dos pruebas nuevas con matchers no instalados; se sustituyeron por aserciones equivalentes sobre textContent/value/disabled. Dos ejecuciones siguientes 36/37 por timeout de 5 segundos del escenario existente que completa factura y dos activos. Se amplió solo ese test a 15 segundos conservando todas sus acciones/aserciones; ejecución final 37/37. No se eliminaron casos ni se debilitaron reglas. La ejecución inicial de fase roja no conserva aquí un resultado completo verificable y no se contabiliza como evidencia.

Diez pruebas backend nuevas: seis de POST agrupado, tres de asociación directa y una de concurrencia API. Verifican ausencia de nuevas filas/revisiones/auditorías ante rechazo, conservación de movimientos y facultad, snapshots, moneda histórica, conflicto por adquisición existente, fechas, ids repetidos, campos reservados, activo inexistente y rollback ante violación SQL real. Los tests concurrentes compiten por las mismas fichas y envían ids en orden inverso: exactamente una transacción acepta.

No se ejecutó migrate contra la base local ni se modificó .env. El runner crea y elimina únicamente su clúster temporal aislado. Pendientes históricos y funcionales de T001–T007 y tareas T011–T018 permanecen fuera del cierre.

## Donaciones T011–T013 — validación real 2026-11-04

Entorno: Windows/PowerShell del proyecto, venv backend y runner privado PostgreSQL del proyecto. Nunca SQLite ni base PostgreSQL local. Feature seleccionada con SPECIFY_FEATURE_DIRECTORY=specs/003-fichas-adquisiciones y SPECIFY_FEATURE_NO_PERSIST=1. Prerrequisitos resueltos al directorio correcto; checklist requirements 10/10, sin modificar marcadores. .specify/extensions.yml ausente al inicio y al cierre: sin hooks registrados.

Comandos desde raíz salvo npm desde frontend:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_donations --verbosity 0
# Antes de implementar items: 8/8 PASS, comportamiento de activos nuevos ya existente.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_donations.DonationExistingItemsTests --verbosity 0
# Fase roja: 5/5 FAIL por guardia 503; el caso SQL no alcanzaba la escritura.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_donations --verbosity 0
# Tras implementar items: 13/13 PASS, 1.037 s.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 0
# Intermedio 148/148 PASS; final, tras cubrir estimaciones iniciales <=0:
# 149/149 PASS, 13.621 s. System check sin incidencias.
npm test -- --run src/tests/donation.test.tsx
# Fase roja: 7/7 FAIL por interfaz pendiente.
# Intermedio: 5/7 PASS, 2 FAIL detectaron panel App y ficha omitidos; ambos corregidos.
npm test -- --run
# Suite intermedia 44/44 PASS. Con dos casos adicionales: 46/46 PASS.
# Última ejecución final: 10 archivos, 46/46 PASS, 31.57 s.
npm run build
# Final: TypeScript --noEmit + Vite PASS, 26 módulos.
& ./backend/.venv/Scripts/python.exe -m pip check
# No broken requirements found.
git diff --check
# Exit 0, solo avisos LF/CRLF.
~~~

Cobertura nueva backend (15 métodos): donación de uno y varios activos, referencia/tipo compartidos, valores separados, USD histórico ante cambio de setting, fechas conocidas/desconocidas, rechazo estricto de factura/campos reservados, ausencia de escrituras en errores, decisiones pendientes explícitas, identidad duplicada, rollback SQL real por CHECK y unicidad, permisos Gestor/Operador/sin rol/anónimo y sesión con CSRF. Items existentes comprueban snapshot antes/después, autor, revisión global, conservación de facultad y Movement e inhabilitación de rectificación previa. Carreras con conexiones reales separadas: altas de identidad igual y asociaciones iniciales con ids invertidos; exactamente un 201 y un 409.

Cobertura nueva React (9 métodos): dos altas con respaldo único, payload estimated_value/revisión para ficha existente, campos específicos sin factura, errores junto al campo/conservación, doble envío, tipo de documento incompatible, navegación y reapertura App, ficha de donación, rechazo de activo sin éxito ficticio y respuesta de red incierta sin reintento. Cliente HTTP/CSRF real con fetch simulado únicamente en pruebas. Sin prueba manual de navegador ni recorrido contra instalación local: NO EJECUTADO.

Regresión completa incluye compras y módulos anteriores 002/008, migración/integridad y gateway. Esto no prueba import_assets con proveedor real de 003: sigue DEPENDENCIA NO INTEGRADA. No se modificaron migraciones; las pruebas de esquema existentes se ejecutaron en el runner temporal. No se ejecutó makemigrations/manage.py migrate contra la configuración local.

Resultado final: cero fallos en suites ejecutadas. T011 parcial por cierre funcional pendiente; T012 y T013 completas en el contrato aprobado y probado. Cero/negativos, fecha documental, adaptación CSV, conversión de origen y protocolo PATCH compartido permanecen sin decisión/implementación integral; las suites verdes no los aprueban.

## T014–T017 — evidencia real 2026-11-04

Preflight: Alex_Sigcho_Feature verificada, 44 rutas con cambios previos conservadas; prerequisitos con FEATURE_DIR absoluto correcto y selección sin persistencia; checklist requirements 10/10; .specify/extensions.yml ausente al inicio y cierre. Entorno del proyecto Windows/PowerShell, venv existente y PostgreSQL privado temporal del runner. Sin consultas/mutaciones de datos locales.

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_metadata_edit --verbosity 0
# Inicial: 5 pruebas, 3 PASS y 2 ERROR por funciones de integración todavía ausentes.
# Tras implementar frontera: 5/5 PASS.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_metadata_edit.CustodianEditTests --verbosity 0
# Fase roja: 4/4 FAIL por PATCH 503; el caso SQL no alcanzaba la escritura.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_metadata_edit --verbosity 0
# Tras servicio real de custodio: 9/9 PASS.
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 0
# Intermedios: 154/154 y 161/161 PASS.
# Final tras caso de error real de guardia/catálogo: 162/162 PASS, 11.720 s.
# System check sin incidencias.
npm test -- --run src/tests/asset-edit.test.tsx
# Inicial: 3/3 FAIL por interfaz pendiente.
# Posterior: 2 fallos de prueba por pulsar texto de código en vez del botón real de ficha; corregidos sin quitar aserciones.
# Nuevos custodios: 5 PASS y 2 FAIL por interfaz todavía pendiente.
# Tras implementación: 7/7 PASS.
npm test -- --run
# Primera completa: 49 PASS, 2 FAIL y 1 error no controlado del mock Operador.
# Final: 11 archivos, 53/53 PASS, 31.91 s, sin errores no controlados.
npm run build
# Final: tsc --noEmit + Vite PASS, 30 módulos.
git diff --check
# Exit 0; solo avisos de conversión LF/CRLF.
~~~

Cambios de pruebas existentes justificados:
- PATCH custodio incompleto ahora devuelve 400 en vez de 503; conserva comprobaciones de perfil y auditoría sin escrituras.
- Prueba de Operador ahora espera únicamente /auth/me y /operator/faculties, mantiene prohibición de alta/consultas ordinarias. El mock anterior devolvía una sesión donde ahora se solicita una lista y provocó rows.map is not a function; se ajustó al contrato y el componente rechaza respuestas de catálogo no confirmables.
- Se restauró el span de autor histórico para conservar la presentación y aserción existente en queries.test.tsx.
- Una espera de catálogo en el test se cambió a findByRole para esperar la respuesta asíncrona; no se cambió el criterio funcional.

13 métodos backend nuevos: edición de activo y revisión global; identidad duplicada/campos reservados; rollback SQL real de activo/línea/revisión; facultad bloqueada con proveedor ausente; guardias pendiente/permitida y rollback aislados; error OperationalError de proveedor propagado y lectura operador con inactivas; cuatro casos de custodio (historia/auditoría, validación/conflicto/duplicados, rollback SQL, roles/CSRF/inmutabilidad SQL); tres carreras con conexiones PostgreSQL independientes. Cada carrera confirma exactamente un 200 y un 409. Caso de facultad usa guardia sustituida solo en tests.

Siete métodos React nuevos: revisión de diferencias antes de PATCH, historial combinado sin perder movimientos, catálogo de Operador sin inventario, revisión obsoleta sin reintento ni éxito ficticio, catálogo rechazado conserva entrada, custodio envía snapshot/motivo, perfil obsoleto conserva borrador. Fetch simulado solo en tests; transporte CSRF/PATCH real del cliente.

FR cubiertos: FR-001–004, FR-005/006/016 en alcance aislado de catálogo/facultad, FR-013–015. La regresión incluye compras, donaciones, custodia, condiciones, rectificación, CSV y expansión de esquema. La inmutabilidad ORM/SQL de auditorías y protecciones de dominio existentes siguen cubiertas por suite completa; caso nuevo verifica UPDATE/DELETE de evidencia real de custodio rechazados en PostgreSQL temporal.

Limitaciones: proveedor real 005 y aplicación real import_assets de 008 NO INTEGRADOS; cambio posterior de facultad NO HABILITADO en producción; edición documental compartida y políticas previas siguen pendientes. Recorrido manual de navegador/local NO EJECUTADO. No se generaron ni aplicaron migraciones nuevas. Suites verdes no cierran esos límites.


</details>
