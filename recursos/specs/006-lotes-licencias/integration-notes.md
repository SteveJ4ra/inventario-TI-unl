# Integración de 006

Fecha: 2026-11-04. Rama: feature/anderson-006-lotes-licencias.

Commit base obtenido mediante `git rev-parse origin/develop` después de fetch: `4247cc8998ed810fdb6462941d85f3324260a2ec`. Contiene 002 (PR #9, 02cb26c), SDD (PR #10) y 008 (PR #14). No se fusionan ramas de implementación ajenas.

## Proveedores y consumidores

- 002 real presente: modelos de activos/custodios/movimientos, Gestores, sesión/CSRF, formato de error y cliente web.
- 006 no depende de Facultad/adquisiciones, mantenimiento ni bajas; no se agregan FK a esos paquetes.
- 008 real presente. Se publica SoftwareLicenseLot/LicenseLotAudit y `inventory.license_services.import_license_lots(actor=..., rows=[valores...])`, además del validador reutilizable.
- Ajuste mínimo en imports/gateways.py: validate_license_lots delega al validador de 006 y mantiene sus errores por fila. El parser, batch, confirmaciones y aplicación de 008 se conservan.
- Integración real de lotes con 008 comprobada: preview, dos confirmaciones, idempotencia, rango DB y rollback si falla segunda fila. No se usa FakeGateway en estas pruebas.
- 003 aún ausente: importación de activos sigue sin proveedor y puede responder 503. No se elimina esa protección ni se simula adquisición/facultad. No bloquea 006.

## Archivos compartidos

Backend: models.py, services.py, serializers.py, views.py, urls.py y el consumo mínimo desde imports/gateways.py. Se agrega license_services.py como frontera esperada por 008. Runner test_postgres.py corregido para sockets privados Linux, conservando aislamiento.

Frontend: App.tsx, api.ts (PATCH), types.ts, Form.tsx (etiquetas de error) y styles.css. Se agregan LicenseLots, LicenseLotForm y LicenseLotDetail; sin dependencias frontend nuevas ni cambios de lockfile.

## Grafo y estado de migraciones

`0001_initial → 0002_integrity → 0003_importbatch → 0004_license_lots → 0005_license_lot_audit_immutable`.

0004 crea tablas/restricciones/FK de licencias; 0005 crea función/trigger de inmutabilidad. SQL revisado; no modifica registros existentes. Aplicadas en PostgreSQL efímero y en DB local tras migrate --plan/sqlmigrate. Hashes del contenido legado conservados; nuevas tablas locales vacías. `makemigrations --check --dry-run`: sin cambios pendientes. En integración futura revisar colisiones de nombres/grafo sin renombrar migraciones ya aplicadas.

## Compatibilidad y regresiones

72 pruebas backend PASS: 27 de 006 más 45 existentes. 16 puras de 008 PASS. 33 frontend PASS y build PASS. Navegador real con dos gestores y DB aislada PASS. Contratos y límites detallados en [validation.md](validation.md).

La fecha de negocio se obtiene de timezone.localdate() en la zona activa; settings base usa UTC. Se preserva ese valor global de 002. El navegador presenta horas de auditoría en Guayaquil y fechas de vigencia sin convertir de zona.

## Actualización puntual de seguridad

Anderson autorizó actualizar únicamente DRF a 3.18.2 y repetir las pruebas. Se modificó una línea de backend/requirements.txt y se instaló con --no-deps; la comparación de paquetes del entorno confirmó que solo cambió djangorestframework (3.16.1 → 3.18.2). Django, psycopg y las demás versiones siguen iguales; package-lock no cambia. Pruebas completas, navegador real, pip check, makemigrations y auditorías repetidas con la instalación actual: correctas; pip-audit sin avisos conocidos. Se conserva la evidencia histórica del hallazgo inicial en validation.md. El cierre se incorpora al séptimo commit, manteniendo siete commits. La publicación fue autorizada posteriormente por Anderson.

## Pendientes concretos

1. Los otros integrantes deben reinstalar requirements para usar DRF 3.18.2 y reproducir las regresiones antes de integrar; no es una actualización global del stack.
2. Otro integrante revisa el diff y reproduce quickstart; Anderson realiza aceptación manual. Las cinco revisiones de Codex no sustituyen esto.
3. Cuando 003 esté integrado, coordinación valida la modalidad CSV de activos y compatibilidad conjunta; 006 ya expone su proveedor real de lotes.
4. Revisión y decisión manual sobre el PR hacia develop por otro integrante. La publicación de la rama y creación del PR ya están autorizadas; [pr-description.md](pr-description.md) contiene el cuerpo de entrega. La URL concreta se comunica tras la respuesta real de GitHub.
5. Ratificación de Constitución/alcance por el equipo y configuración de producción siguen pendientes; no se atribuyen a estas pruebas locales.

No hay bloqueo de ejecución funcional de 006 por un proveedor ausente. La actualización resuelve los avisos conocidos detectados por el escaneo de dependencias. Revisión humana, configuración de producción e integración global siguen pendientes; no se declara seguridad absoluta ni certificación OWASP.
