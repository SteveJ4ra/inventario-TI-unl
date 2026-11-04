# Implementación de 006 — Lotes de licencias

Fecha: 2026-11-04 (America/Guayaquil). Desarrollo local autorizado por Anderson con asistencia de Codex. Revisión humana y ratificación de Constitución pendientes. La implementación se mantuvo local inicialmente; Anderson autorizó después publicar la rama propia y abrir el PR hacia develop. No se autoriza fusión automática.

## Análisis previo y siete partes

Base verificada tras `git fetch origin`: `4247cc8998ed810fdb6462941d85f3324260a2ec` (develop, 002 y 008 integrados). Rama propia: `feature/anderson-006-lotes-licencias`. Identidad Git: configuración existente del alumno, sin modificarla.

Se leyeron la guía anderson.md, README/CONTRIBUTING, documentación backend/frontend, Constitución propuesta, alcance/decisiones/contratos transversales/análisis cruzado, los artefactos de 006, contrato 002 y código compartido. No hay skills speckit-analyze/implement disponibles en esta sesión; el análisis se realiza sobre archivos. Spec Kit devuelve FEATURE_DIR terminado en 006-lotes-licencias con NO_PERSIST=1.

Plan de siete commits locales:

1. Corregir el runner PostgreSQL y comprobar la base existente (preparación de T001/T010).
2. Agregar modelos, restricciones, auditoría inmutable y migraciones (T001–T003).
3. Agregar validadores y servicios transaccionales reutilizables (T004/T005/T008).
4. Agregar API, filtros, permisos y pruebas de seguridad/concurrencia (T001/T006/T010/T013).
5. Agregar pantalla de lotes, edición e historial (T007/T009).
6. Agregar pruebas de interfaz y revisar integración (T011/T013).
7. Documentar resultados y cinco revisiones finales (T012 y cierre de evidencia).

## Parte 1: entorno de pruebas

Python 3.13.14; Django 5.2.18; DRF 3.16.1; PostgreSQL 17.11; Node 24.18.0; npm 11.16.0; PowerShell 7.6.9. Se conservan requirements y package-lock.

El runner fallaba antes de ejecutar pruebas: `could not create lock file /var/run/postgresql/.s.PGSQL.<puerto>.lock: Permission denied`. Ahora usa un socket dentro del directorio temporal privado en POSIX y muestra el log del servidor con la contraseña efímera redactada. La contraseña temporal tiene permisos 0600. No cambia .env ni permisos del rol de aplicación.

Comando: `PG_BIN=/usr/lib/postgresql/17/bin PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/tools/test_postgres.py`.

Resultado real: 45 pruebas existentes PASS en PostgreSQL temporal 17.11, con migraciones y carreras reales. Es una línea base, no evidencia de 006 implementado.

## Parte 2: modelos y migraciones (T001–T003)

Se agregan SoftwareLicenseLot y LicenseLotAudit sin enlaces a activos, facturas o custodios. Enteros no negativos; uso <= compradas; modalidad limitada a USER_SEAT/DEVICE_SEAT; inicio no nulo y fin >= inicio. Remanentes y estado se calculan. El día fin es inclusivo y se usa `timezone.localdate()` de la zona configurada por Django (UTC en esta base); no se cambia globalmente la zona de 002.

Migraciones nuevas 0004_license_lots y 0005_license_lot_audit_immutable después de 0003_importbatch, sin modificar migraciones existentes. El trigger impide UPDATE/DELETE de auditoría incluso con QuerySet o SQL directo; revisión única por lote/evento. La etiqueta del autor conserva el nombre registrado.

Prueba focalizada real: `PG_BIN=/usr/lib/postgresql/17/bin PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/tools/test_postgres.py inventory.tests.test_license_lots --verbosity 1`: 3 pruebas PASS (límites temporales, integridad DB, inmutabilidad y unicidad). Las migraciones se aplicaron solo en DB efímera; la DB de desarrollo conserva su estado hasta revisión del plan final.

## Parte 3: validación y servicios (T004/T005/T008)

Se agregan entradas/salidas explícitas; campos desconocidos rechazados; cantidades JSON estrictamente enteras (sin bool, float ni cadenas), rango 0–2147483647 de PostgreSQL integer. Edición parcial fusionada con valores vigentes; expected_revision requerido. Edición vacía o sin cambios devuelve 400 sin eventos ficticios.

Servicios de alta/edición verifican Gestor, validan datos y guardan auditoría de alta (revisión 0) y cada modificación real. Edición usa select_for_update y comparación de revisión; un conflicto no escribe. Datos antes/después incluyen todos los campos editables y revisión; autor/hora se generan en servidor.

`inventory.license_services.import_license_lots(actor=..., rows=[valores...])` publica la firma real consumida por 008; prevalidación de todas las filas y transacción íntegra, sin parser/confirmaciones CSV nuevos. La importación puede crear lotes iguales: no se inventó unicidad de producto/proveedor.

Prueba focalizada: mismo runner con `inventory.tests.test_license_lots --verbosity 1`, 8 PASS. Incluye rechazo sin escrituras, validación desde servicios, autor conservado y rollback de alta/edición al fallar auditoría. El mock se usa solo para provocar el fallo; la persistencia y rollback son PostgreSQL reales.

## Parte 4: API y controles de seguridad (T001/T006/T010/T013)

Endpoints de lista/alta/detalle/PATCH/historial bajo /api/license-lots/. Lista e historial limitados a 50 filas por página; búsqueda producto/proveedor y filtros license_model/temporal_status. Un día local calculado por petición mantiene consistentes filtro y estado devuelto. Se conserva HTTP 403 y formato de errores 002; sin PUT/DELETE ni escritura de historia.

Primera ejecución completa: 67 pruebas, 1 error. Una entrada JSON escalar provocó un ValueError en el tratamiento de errores heredado. Se corrigió el serializador de 006 para devolver non_field_errors estructurado, sin cambiar endpoints de compañeros. Segunda ejecución: 67 PASS.

La suite nueva comprueba sesiones reales con CSRF y origen ajeno, roles sin permiso (incluido superusuario sin Gestores), campos de autor/estado/snapshots manipulados, tipos/rangos/JSON malformado, 404/405, búsqueda tipo SQL injection, paginación y fecha local en dos zonas. La carrera real con dos conexiones permite una sola edición (200 y 409) con auditoría consistente. 008 se probó con su gateway real, CSV/doble confirmación/aplicación e idempotencia sobre SoftwareLicenseLot, no fake. Se conserva pendiente la integración de activos 003 ajena al alcance.

## Parte 5: pantalla web (T007/T009)

Se agrega Licencias a la navegación existente, incluida la vista estrecha. Lista paginada, búsqueda/filtros, alta, detalle, edición parcial vía PATCH y auditoría paginada con antes/después de los siete campos. Formulario exige inicio, permite fin nulo y cantidades cero; muestra remanentes calculados. Lotes vencidos se etiquetan y se aclara que el conteo no equivale a puestos utilizables.

Se reutilizan Form/ErrorNotice, estilos y cliente de sesión/CSRF. El cliente incorpora PATCH y valores null sin cambiar POST existentes. Conflicto 409 recarga ficha/historial y cierra la edición obsoleta sin reintentar la escritura. React representa valores como texto; sin HTML dinámico. Consultas se cancelan al cambiar de vista y los datos privados se desmontan al cerrar sesión.

Verificación tras integrar pantalla: las 20 pruebas frontend existentes PASS; TypeScript y build Vite PASS. Pruebas específicas de 006 quedan para parte 6. No se atribuye un recorrido manual de la pantalla nueva al alumno.

## Parte 6: integración, interfaz y revisiones de seguridad (T011/T013)

Se agregan 13 pruebas de interfaz: obligatorios/cero/fin nulo, rechazo de cantidades/fechas, errores de campos, bloqueo de doble envío, PATCH con CSRF/sesión/revisión, búsqueda/filtros/páginas, etiquetas y texto HTML escapado, alta/edición/historial, 409 sin reintento, historial paginado, error de red, 403 y logout. Total frontend: 33 PASS; build PASS.

Revisión de integración: el gateway existente de 008 comprobaba solo la presencia del modelo. Se agrega únicamente delegación al validador público de 006 para rechazar cantidades fuera del rango DB antes de confirmar. No cambia parser, estados ni confirmaciones de CSV. Se prueba gateway real y rollback de ambas filas/auditorías al fallar la segunda; el batch sigue confirmable y puede reintentarse. La prueba de rechazo detectó una importación faltante al reducir el diff del archivo compartido; se corrigió y se repitió toda la suite.

Revisión de entradas: JSON solo UTF-8 y 16 KiB, lectura acotada aunque falte Content-Length; respuesta no-store. Un nombre de campo con surrogate Unicode causaba 500 al representar el error; se valida el nombre antes de generar fields y se comprueba respuesta 400. Codificaciones de compresión, Unicode inválido, anidación y JSON no objeto se rechazan sin escribir. Suite final en el stack original: 72 backend PASS (27 nuevas de 006 + 45 de la base), 16 pruebas puras de 008 PASS.

Recorrido automático en Google Chrome 156.0.8078.47 con `backend/tools/smoke_license_lots.py`: PASS en PostgreSQL 17 efímero. Dos gestores ficticios, sesión/CSRF reales, alta cero sin fin, edición auditada, vencido con remanentes, conflicto 409 real, móvil 375px sin desborde y logout. El primer intento falló al localizar el selector de modalidad; se añadió nombre accesible explícito y el recorrido posterior pasó. Captura móvil inspeccionada por Codex, solo datos ficticios; no se agrega al repositorio. No equivale a aceptación manual del alumno ni a revisión humana independiente.

Tras revisar `migrate --plan` y `sqlmigrate` 0004/0005, se aplicaron ambas a la DB local. Comparación de hashes de registros de Asset, Custodian, Movement, ImportBatch y User antes/después: contenido conservado. Había 0 registros de negocio y 1 cuenta; no se crearon cuentas/lotes ficticios en la DB local. Nuevas tablas vacías.

Auditoría inicial: npm audit sin avisos; Bandit sin hallazgos medios/altos en código backend de inventario. pip-audit detectó cinco avisos en DRF 3.16.1. La decisión sobre actualización se solicitó al alumno: no se presenta el escaneo inicial como aprobado. Se preparó una variante temporal de requirements cambiando solo DRF a 3.18.2: 72 pruebas PASS y pip-audit sin vulnerabilidades conocidas en esa variante; no cambia por sí sola la dependencia del proyecto.

## Parte 7: evidencia, tareas y cinco revisiones (T012)

Se actualizan README raíz/backend/frontend, spec/plan/modelo/contratos, tasks, quickstart y estado del plan de validación sin eliminar escenarios. Se entregan validation.md, integration-notes.md, reviews.md y pr-description.md. Las cinco pasadas están documentadas por requisitos/contratos, seguridad, DB/concurrencia, interfaz y reproducción/entrega. Revisión humana y aceptación manual continúan pendientes.

Se verificaron enlaces locales, T001–T013 sin duplicados, cinco revisiones, diff --check, ausencia de valores privados del .env en el diff y exclusión de .env/venv/node_modules. En la verificación inicial se conservaron requirements y lockfile y se dejó constancia del escaneo fallido de DRF 3.16.1. El cierre autorizado de seguridad se documenta a continuación; el lockfile sigue sin cambios.

Commits anteriores de esta entrega: 2388e69 (runner), 84617ce (modelos), 3533967 (servicios), 2056706 (API), 88feea9 (web), cecf509 (pruebas/seguridad). El séptimo commit contiene este cierre documental. Son siete commits en la rama propia. Anderson autorizó su publicación y la creación del PR hacia develop; el texto está preparado en pr-description.md. No se realiza merge automático.


### Cierre autorizado de seguridad dentro del séptimo commit

Anderson confirmó actualizar solo DRF a 3.18.2 y repetir las pruebas. Se fijó esa versión en backend/requirements.txt y se instaló con `backend/.venv/bin/python -m pip install --no-deps 'djangorestframework==3.18.2'`. Se comparó el inventario de distribuciones antes/después: únicamente djangorestframework pasó de 3.16.1 a 3.18.2; no se actualizaron otros paquetes ni el lockfile frontend.

Resultados repetidos con el entorno principal actualizado: 72 pruebas backend, 33 frontend y 16 puras PASS; build, check, makemigrations --check --dry-run y pip check PASS. Navegador real nuevamente PASS. pip-audit sin vulnerabilidades conocidas; npm audit sin avisos; Bandit sin hallazgos medios/altos. Las advertencias de despliegue HTTP local/DEBUG y la revisión humana siguen documentadas.

Se actualizan los estados y evidencias de las cinco revisiones para distinguir el hallazgo histórico de la corrección aplicada. Este cierre se incorpora mediante amend al séptimo commit propio sin publicar, conservando exactamente siete commits locales. Hasta ese cierre inicial no se había publicado la rama; la publicación fue autorizada posteriormente por Anderson.


### Entrega Git autorizada

Anderson solicitó publicar los commits y crear el pull request. Antes de publicar se verificó árbol limpio, siete commits propios y `git fetch origin`: develop permanecía en 4247cc8998ed810fdb6462941d85f3324260a2ec, sin cambios adicionales que integrar. La credencial Git configurada pertenece a AndersonC15 y tiene permiso push; no se imprime ni se guarda en el código. La rama remota propia y un PR previo no existían al comprobarlos. Se usa Git y la API oficial de GitHub porque gh no está instalado.

La entrega remota usa la rama feature/anderson-006-lotes-licencias y base develop, con solicitud de revisión a un colaborador verificado. La URL y el estado final se informan a partir de la respuesta de GitHub. Se mantienen siete commits, sin force push, autoaprobación o merge automático. La revisión humana, aceptación manual y ratificación del equipo no se sustituyen por esta publicación.
