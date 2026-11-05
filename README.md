# Inventario de Tecnologías de Información · UNL

Proyecto académico del Grupo 5 para registrar y consultar activos tecnológicos y conservar la trazabilidad de su custodia. Se desarrolla por incrementos mediante Spec-Driven Development (SDD) con GitHub Spec Kit.

## Base implementada 002

API Django REST Framework y pantalla React + TypeScript con:

- Acceso de gestores autorizados, con iguales permisos sobre todo el inventario.
- Registro de activos con código TI automático, identificación individual y prevención de duplicados por marca/modelo/serie.
- Registro de personas custodias sin cuenta de acceso.
- Listado, ficha, búsqueda parcial y filtros combinados.
- Entregas, devoluciones y cambios reales de condición con motivo cuando corresponde.
- Historial con autoría y rectificación del último movimiento elegible, conservando el original y restaurando la situación anterior.
- Controles de concurrencia, CSRF y restricciones de integridad en PostgreSQL.

Las seis categorías y las reglas funcionales provienen de las respuestas documentadas de Steven; la FPGA fue únicamente un ejemplo. No se implementan edición general, eliminación, órdenes de mantenimiento, portal de custodios, reportes ni aplicación móvil en este incremento.

## Paquete 004 · Novedades y mantenimiento

La ficha permite reportar y resolver daños y observaciones, iniciar y cerrar mantenimiento, reportar pérdida o robo y recuperar activos. Conserva el historial de 002 y suma las nuevas transiciones con autoría y revisión. Un activo en taller no se puede entregar. El reporte de pérdida o robo conserva el último estado conocido y la recuperación mantiene el código original.

La rama de 004 requiere las migraciones `inventory.0004_asset_lifecycle_events` y `inventory.0005_asset_transition_evidence`. Para reproducir el recorrido con datos ficticios, consulta el [quickstart de 004](specs/004-novedades-mantenimiento/quickstart.md). Los resultados y sus límites están en la [validación de 004](specs/004-novedades-mantenimiento/validation.md).

## Ejecutar localmente

Requisitos: Python 3.13, PostgreSQL 17 y Node.js 22.23.1 o compatible con las versiones fijadas. Preparación completa de base de datos y .env: [backend/README.md](backend/README.md). Frontend: [frontend/README.md](frontend/README.md).

En una instalación ya configurada, PowerShell desde la raíz:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py migrate
& .\backend\.venv\Scripts\python.exe backend/manage.py create_gestor
npm.cmd --prefix frontend ci
```

El comando create_gestor pide usuario y contraseña localmente; no hay credenciales predeterminadas. No vuelve administrador general al gestor. Si ya tienes un gestor autorizado no necesitas crear otro.

En dos terminales:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

```powershell
cd frontend
npm.cmd run dev
```

Abrir [la pantalla web local](http://127.0.0.1:5173/). La API está bajo /api/ en el backend; la raíz de Django no sirve la pantalla React. En Linux se usa backend/.venv/bin/python. No copiar encima del .env privado existente.

## Pruebas y estado comprobado

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
```

El runner crea PostgreSQL temporal privado en loopback, usa credenciales efímeras, ejecuta las pruebas y lo detiene/elimina. Requiere binarios PostgreSQL 17 con ICU; PG_BIN permite indicar su carpeta bin. No concede CREATEDB al usuario de la aplicación ni cambia backend/.env. Ejecutarlo como usuario normal, no como root en Linux.

Validación automatizada del 1 de noviembre de 2026: **28 pruebas backend, 17 pruebas frontend y compilación correctas**. El 20 de octubre se verificó además el recorrido real en navegador con dos gestores ficticios, custodia, rectificación, búsqueda/filtros y conflicto de un formulario obsoleto. Evidencia y límites: [validation.md](specs/002-registro-consulta-activos/validation.md). La reproducción por otro integrante y la revisión por pares siguen pendientes; no se declara despliegue productivo.

## Ruta SDD y organización

| Artefacto / carpeta | Propósito |
|---|---|
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | Principios propuestos; ratificación del grupo pendiente. |
| [specs/001-inventario-ti/](specs/001-inventario-ti/) | Contexto inicial conservado. |
| [Decisiones del incremento](docs/sdd/decisiones-incremento-registro-consulta.md) | 36 decisiones confirmadas y su evidencia. |
| [spec.md](specs/002-registro-consulta-activos/spec.md) | Qué se requiere, reglas y aceptación. |
| [plan.md](specs/002-registro-consulta-activos/plan.md) | Cómo se diseñó, modelo y contratos. |
| [tasks.md](specs/002-registro-consulta-activos/tasks.md) | Desglose y estado real de 38 tareas. |
| [quickstart.md](specs/002-registro-consulta-activos/quickstart.md) | Recorrido reproducible de validación. |
| backend/inventory/ | Modelos, servicios, API, comandos y pruebas. |
| frontend/ | Pantalla web, cliente API y pruebas. |

Se siguió specify → clarify → plan → tasks → analyze → implement. Las reglas de negocio fueron aclaradas antes de programar; el análisis detectó y corrigió con aprobación de Steven una dependencia circular en las tareas de pruebas. La implementación contó con asistencia de Codex; la revisión humana del equipo continúa siendo necesaria.

## Seleccionar el incremento en Spec Kit

El marcador .specify/feature.json es local y está ignorado por Git. En una copia nueva, antes de usar las skills de Spec Kit, seleccionar explícitamente el directorio activo en la sesión PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "specs/002-registro-consulta-activos"
```

Esto conserva la rama Git feature/registro-consulta-activos; el identificador lógico es 002-registro-consulta-activos. No requiere reinicializar Spec Kit ni reemplazar Copilot por Codex. Los scripts incluidos son PowerShell; en Linux requieren pwsh. Esta configuración de Spec Kit es independiente de ejecutar la aplicación con Python y npm.

## Colaboración

Ramas main/develop/feature; contribuciones y revisión antes de integrar según [CONTRIBUTING.md](CONTRIBUTING.md). No publicar .env, contraseñas, datos institucionales o archivos temporales. Mantener la revisión de este incremento en su rama feature sin atribuir aprobación al equipo antes de obtenerla.

## Paquete 003 — estado de entrega

Fichas, facultades y adquisiciones se desarrollan en Alex_Sigcho_Feature para integración hacia develop. El alcance implementado incorpora compras/donaciones compartidas, Operador, edición auditada e importación real de adquisiciones mediante 008. La entrega sigue parcial por transición histórica, decisiones funcionales y proveedor 005 ausente; no se declara lista para merge integral.

Consultar [estado por tarea](specs/003-fichas-adquisiciones/tasks.md), [validación](specs/003-fichas-adquisiciones/validation.md), [integraciones pendientes](specs/003-fichas-adquisiciones/integration-notes.md) y [quickstart aislado](specs/003-fichas-adquisiciones/quickstart.md). La migración 0004 solo se ha probado en PostgreSQL temporal; no se aplicó a la base local. El cuerpo del PR Draft está preparado en [pr-description.md](specs/003-fichas-adquisiciones/pr-description.md), sin publicación.
