# Inventario de Tecnologías de Información - UNL

Backend académico del Grupo 5, desarrollado por incrementos con Spec-Driven Development (SDD) y GitHub Spec Kit. La consolidación de Unidad 1 parte de develop b60f52f, integra los módulos 002-008 y completa contrato v1/OpenAPI, observabilidad, BPMN y portal Quarto mediante el incremento técnico 009.

## Alcance del backend

| Módulo | Funciones y contrato |
| --- | --- |
| 002 | Registro/consulta de activos, custodios, entregas/devoluciones, condición, historial y rectificación. [Especificación](specs/002-registro-consulta-activos/spec.md) |
| 003 | Compras/donaciones compartidas, importes por activo, facultades y edición auditada. [Especificación](specs/003-fichas-adquisiciones/spec.md) |
| 004 | Daños/observaciones, mantenimiento, pérdida/robo y recuperación. [Especificación](specs/004-novedades-mantenimiento/spec.md) |
| 005 | Bajas, aprobación por revisor de otra facultad y administración técnica de revisores. [Especificación](specs/005-bajas-aprobacion/spec.md) |
| 006 | Lotes finitos de licencias con cantidades, vigencia y auditoría. [Especificación](specs/006-lotes-licencias/spec.md) |
| 007 | QR SVG sin datos personales, destino canónico y acceso protegido. [Especificación](specs/007-qr-activos/spec.md) |
| 008 | Importación CSV de activos y licencias con validación completa, dos confirmaciones y aplicación atómica. [Especificación](specs/008-importacion-csv/spec.md) |

Gestores con acceso global acordado; operador con facultades/cuentas revisoras; revisor limitado a solicitudes asignadas e independencia de facultad; custodios sin cuenta. Sesiones de treinta minutos absolutos, CSRF en escrituras y cinco fallos por cuenta/IP en quince minutos. No hay auto-registro ni claves de activación de licencias.

## Ejecutar con Docker Compose

```powershell
python deploy/prepare_secrets.py
docker compose build web tests
docker compose up -d --wait --no-build web
docker compose exec web python manage.py create_gestor
```

Abrir http://localhost:8005/api/docs/ . La API y documentación se sirven con Gunicorn, DEBUG=false y usuario sin root. PostgreSQL usa un rol limitado, datos persistentes y secretos montados como archivos. No hay contraseña predeterminada; los comandos piden credenciales localmente.

[Guía de despliegue, pruebas y operación](deploy/README.md). El HTTP se limita a loopback; no se declara un servidor público con TLS. El frontend React existente se ejecuta aparte y PUBLIC_APP_URL debe apuntar a su dirección para navegar desde el QR.

```powershell
docker compose --profile test run --rm tests --pytest -q
docker compose --profile test run --rm tests makemigrations --check --dry-run
```

Resultado local de consolidación: 378 pruebas con pytest-django y 284 subcasos, incluidas 37 pruebas aisladas; 66 comprobaciones HTTP sobre Gunicorn. Contrato completo: 46 rutas y 56 operaciones, con 43 respuestas JSON reales validadas. Respaldo restaurado en base temporal: 34 tablas/212 filas idénticas en conteo y SHA-256. [Evidencia actual](docs/producto-final/evidencia-validacion.json). testdb permanece separado de la base operativa.

## Ejecutar sin contenedores

Python 3.13 y PostgreSQL 17 con ICU. Preparar entorno y .env según [backend/README.md](backend/README.md), sin sobrescribir configuración existente. Ejecutar migraciones y crear gestor solo si corresponde. Arrancar backend con backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000 (en Linux, backend/.venv/bin/python). El frontend requiere Node y sus comandos están en [frontend/README.md](frontend/README.md).

## API y documentación SDD

- [OpenAPI completo vigente](docs/producto-final/openapi.json): /api/v1/ cubre todos los módulos y normaliza JSON con success/message/data/errors/meta. /api/ conserva su contrato histórico. CSV/SVG y HEAD/204/304 respetan su semántica de archivo/HTTP.
- [Dossier técnico](docs/semana-5/dossier-backend.md), [104 requisitos trazados](docs/semana-5/matriz-trazabilidad.md), [bitácora](docs/semana-5/bitacora-integracion.md) y [estándares](docs/semana-5/estandares.md).
- [Arquitectura de semana 3](docs/semana-3/c4-contenedores.puml), [seguridad de semana 4](docs/semana-4/modelo-amenazas.md) y [ADR de despliegue](docs/semana-5/ADR-0501-despliegue-local.md).
- [.specify/memory/constitution.md](.specify/memory/constitution.md) conserva su estado de propuesta; las decisiones funcionales confirmadas están en docs/sdd/. No se atribuyen políticas institucionales a esta entrega académica.

Para seleccionar un incremento en Spec Kit, definir SPECIFY_FEATURE_DIRECTORY con su directorio specs/00X-... en la sesión correspondiente. No reinicializar Spec Kit ni sobrescribir las integraciones Copilot/Codex. El flujo es specify, clarify, plan, tasks, analyze, implement y validate con evidencia.

## Portal Quarto y producto final

Instalar Quarto 1.11.9, ejecutar `quarto render portal` y `quarto preview portal --no-browser`. [Guía operativa](portal/operacion.qmd), [matriz de entrega](docs/producto-final/matriz-entrega.md), [proceso BPMN](docs/producto-final/custodia.bpmn) y [ADR-0901](docs/producto-final/ADR-0901-contrato-y-operacion.md). El portal queda preparado para Pages; la publicación es manual desde develop hacia gh-pages, después de revisión; ver docs/producto-final/publicacion.md. Pages sirve documentación estática, no el backend.

La evidencia de semanas anteriores se conserva como historia del incremento. La referencia actual es docs/producto-final y specs/009-consolidacion-final. CI valida backend, migraciones, OpenAPI/BPMN y render de Quarto al incorporarse a GitHub.

## Colaboración y cuidado de datos

Ramas propias y PR hacia develop según [CONTRIBUTING.md](CONTRIBUTING.md); main permanece fuera de esta integración. No publicar .env, deploy/.secrets, respaldos, credenciales o datos institucionales. No borrar el volumen de Docker para resolver un problema con datos existentes. Las validaciones históricas por módulo se conservan en specs/; el dossier integrado distingue esos registros de la evidencia actual.

El alcance backend no certifica todas las pantallas o navegación móvil. La documentación indica límites del QR/cliente, donaciones e importes y del despliegue público para evitar asumir funcionalidades no confirmadas.

En anfitrión Linux, después de prepare_secrets.py: instalar el paquete acl y ejecutar `bash deploy/prepare_linux_secret_access.sh`. Compose monta archivos y conserva permisos del anfitrión; la ACL permite solo los UID lectores necesarios, sin hacer públicos los secretos. En Docker Desktop/Windows no se aplica este script.
