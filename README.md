# Inventario de Tecnologías de Información - UNL

Backend académico del Grupo 5, desarrollado por incrementos con Spec-Driven Development (SDD) y GitHub Spec Kit. La base integrada 435b0e0 contiene 002-008 y los controles de seguridad de semana 4; esta rama añade el despliegue local reproducible de semana 5.

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
docker compose build web
docker compose up -d --wait --no-build web
docker compose exec web python manage.py create_gestor
```

Abrir http://localhost:8005/api/docs/ . La API y documentación se sirven con Gunicorn, DEBUG=false y usuario sin root. PostgreSQL usa un rol limitado, datos persistentes y secretos montados como archivos. No hay contraseña predeterminada; los comandos piden credenciales localmente.

[Guía de despliegue, pruebas y operación](deploy/README.md). El HTTP se limita a loopback; no se declara un servidor público con TLS. El frontend React existente se ejecuta aparte y PUBLIC_APP_URL debe apuntar a su dirección para navegar desde el QR.

```powershell
docker compose --profile test run --rm tests
docker compose --profile test run --rm tests makemigrations --check --dry-run
```

Resultado comprobado en Docker: 333 pruebas Django/API/contrato, 21 pruebas aisladas de políticas y 16 de importación; 30 respuestas HTTP del recorrido protegido y persistencia después de recrear servicios. [Evidencia y límites](docs/semana-5/validacion.md). Estas pruebas usan testdb separado; no elevan privilegios del usuario operativo. Las instrucciones de las dos suites aisladas están en la guía de despliegue.

## Ejecutar sin contenedores

Python 3.13 y PostgreSQL 17 con ICU. Preparar entorno y .env según [backend/README.md](backend/README.md), sin sobrescribir configuración existente. Ejecutar migraciones y crear gestor solo si corresponde. Arrancar backend con backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000 (en Linux, backend/.venv/bin/python). El frontend requiere Node y sus comandos están en [frontend/README.md](frontend/README.md).

## API y documentación SDD

- [Catálogo de rutas y contratos](docs/semana-5/catalogo-api.md): la API completa conserva rutas /api/; /api/v1/ y su OpenAPI cubren el recorrido base. No se promete un único formato para todos los módulos.
- [Dossier técnico](docs/semana-5/dossier-backend.md), [104 requisitos trazados](docs/semana-5/matriz-trazabilidad.md), [bitácora](docs/semana-5/bitacora-integracion.md) y [estándares](docs/semana-5/estandares.md).
- [Arquitectura de semana 3](docs/semana-3/c4-contenedores.puml), [seguridad de semana 4](docs/semana-4/modelo-amenazas.md) y [ADR de despliegue](docs/semana-5/ADR-0501-despliegue-local.md).
- [.specify/memory/constitution.md](.specify/memory/constitution.md) conserva su estado de propuesta; las decisiones funcionales confirmadas están en docs/sdd/. No se atribuyen políticas institucionales a esta entrega académica.

Para seleccionar un incremento en Spec Kit, definir SPECIFY_FEATURE_DIRECTORY con su directorio specs/00X-... en la sesión correspondiente. No reinicializar Spec Kit ni sobrescribir las integraciones Copilot/Codex. El flujo es specify, clarify, plan, tasks, analyze, implement y validate con evidencia.

## Colaboración y cuidado de datos

Ramas propias y PR hacia develop según [CONTRIBUTING.md](CONTRIBUTING.md); main permanece fuera de esta integración. No publicar .env, deploy/.secrets, respaldos, credenciales o datos institucionales. No borrar el volumen de Docker para resolver un problema con datos existentes. Las validaciones históricas por módulo se conservan en specs/; el dossier integrado distingue esos registros de la evidencia actual.

El alcance backend no certifica todas las pantallas o navegación móvil. La documentación indica límites del QR/cliente, donaciones e importes y del despliegue público para evitar asumir funcionalidades no confirmadas.
