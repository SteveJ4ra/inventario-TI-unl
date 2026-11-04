# Implementación de 006 — Lotes de licencias

Fecha: 2026-11-04 (America/Guayaquil). Desarrollo local autorizado por Anderson con asistencia de Codex. Revisión humana y ratificación de Constitución pendientes. No se publica rama ni PR por instrucción del alumno.

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
