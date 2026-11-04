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
