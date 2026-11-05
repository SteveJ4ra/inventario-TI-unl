# Quickstart: validar 004

Usa datos ficticios en una base de prueba con PostgreSQL 17 e ICU. La [guía del backend](../../backend/README.md) explica el entorno y la provisión interactiva de un Gestor. Comprueba las migraciones con `manage.py showmigrations inventory` y revisa el plan antes de aplicarlo a una base persistente.

## Validación automatizada

Desde la raíz del repositorio en PowerShell, con el entorno Python y las dependencias del frontend instaladas:

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory --verbosity 1
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
```

Para repetir el recorrido real, indica la ruta al módulo de Playwright y al ejecutable de Chrome o Chromium. Ejemplo con el runtime usado en la validación de Windows:

```powershell
$env:VALIDATION_004_PLAYWRIGHT="$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright"
$env:VALIDATION_004_CHROMIUM='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .\backend\.venv\Scripts\python.exe backend/tools/validate_004_browser.py
```

El runner arranca PostgreSQL temporal con ICU, aplica el esquema allí, crea un Gestor y datos ficticios, inicia Django y Vite en loopback y ejecuta Chrome sin interfaz. Usa credenciales efímeras, detiene sus procesos y elimina el clúster temporal al finalizar.

## Recorrido desde la ficha

1. Crea un activo disponible y un custodio ficticio. Registra una entrega.
2. Reporta un daño con el activo asignado. Comprueba la alerta y que la condición y custodia se conservan. Resuelve con una nota y revisa ambos eventos, su autoría y fecha.
3. Devuelve el activo. Inicia un mantenimiento preventivo y verifica la ubicación del taller y el bloqueo de la entrega incluso con condición Operativo.
4. En el cierre, comprueba que se precargó la ubicación previa. Prueba editarla y confirma con «¿Estás seguro?» antes de guardar. Verifica resultado, ubicación y condición.
5. Inicia un **segundo** mantenimiento y reporta un robo en el taller. Comprueba «No localizado», último estado conocido, ausencia de custodia vigente y mantenimiento interrumpido sin resultado. Las acciones incompatibles se ocultan y la API rechaza su ejecución.
6. Confirma la inspección, elige la condición e indica la ubicación de recuperación. Comprueba el mismo código, disponibilidad sin custodio y el mantenimiento previo interrumpido.
7. Revisa el historial unificado por revisión y el historial legado de movimientos. La pérdida y la recuperación no crean devoluciones ficticias.

Los comandos, resultados y casos de integración se detallan en [validation.md](validation.md).

Antes de ejecutar Spec Kit, seleccionar `specs/004-novedades-mantenimiento` siguiendo [el índice SDD](../../docs/sdd/README.md#seleccionar-el-paquete-correcto-en-spec-kit) y verificar FEATURE_DIR. El chequeo solo verifica documentos; no ejecuta implementación ni pruebas de aceptación.
