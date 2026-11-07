# Quickstart 003 — validación aislada y revisión

Estado vigente: implementación parcial verificada, 182/182 backend y 57/57 frontend. Rama Alex_Sigcho_Feature; PR previsto hacia develop y recomendado como Draft. No ejecutar migraciones ni provisión sobre la base local sin revisión previa.

## Validación reproducible sin PostgreSQL local

Desde la raíz, con dependencias del proyecto ya instaladas:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 0
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --manage check
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --manage makemigrations --check --dry-run
& ./backend/.venv/Scripts/python.exe -m pip check
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
git diff --check
~~~

Los comandos npm con --prefix son la variante reproducible desde raíz; la validación registrada ejecutó npm test y npm run build desde frontend. El runner mantiene credenciales y clúster privados temporales y no modifica .env.

## Recorrido preparado para después de revisar el despliegue

Gestor: crear/cargar factura o respaldo, registrar varios activos con facultad, valor y fecha/motivo; consultar historial; corregir ficha/custodio mediante diferencias confirmables. Editar documento compartido obtiene metadatos/revisiones actuales y exige motivo. Un conflicto conserva el borrador y no reintenta automáticamente.

Operador: crear/corregir/activar/desactivar facultades; no recibe permisos ordinarios de Gestor por login. El cambio posterior de facultad permanece bloqueado por falta de 005 real.

008: compras nuevas agrupadas y documentos existentes están integrados. Para donación CSV usar un documento previamente registrado por el flujo aprobado; crear una donación nueva desde support_description continúa bloqueado por decisión humana.

T004: revisar acquisition_preflight y migration-notes/faculty_contract.py.txt. El preflight es solo lectura; la plantilla NO es una migración activa y no debe copiarse al grafo sin mapeo/revisión de escritores. El dato local de 0 activos no sustituye esa revisión en otras instalaciones.

Recorrido manual de navegador: no ejecutado. Resultados y límites completos en validation.md e integration-notes.md.

<details>
<summary>Guías históricas de bloques anteriores; no son autorización de migración local</summary>

# Quickstart: validar 003

**Estado:** pasos de validación futura; implementación aún pendiente.

1. Migrar la base de datos de prueba desde una copia desechable.
2. Provisionar operador con create_operator; iniciar sesión sin permisos de Gestor, crear facultad y probar su cambio auditado.
3. Crear metadatos de factura; registrar dos activos usando su id compartido, total común y valores por línea; comprobar atomicidad y que no se duplica el total.
4. Registrar una donación con respaldo textual compartido y valor estimado por cada equipo.
5. Registrar adquisición con fecha desconocida y motivo; comprobar rechazo si falta el motivo.
6. Editar un campo descriptivo con motivo; verificar antes/después, autor/fecha y ficha actual.
7. Editar correo/nombre de custodio; verificar que movimientos anteriores mantienen snapshots originales.
8. Intentar cambiar ubicación o condición desde PATCH general; se rechaza.
9. Verificar permisos de gestor y operador; el gestor no puede administrar la lista de facultades.
10. Ejecutar validación automatizada de backend/frontend planificada en validation-plan.md al implementar.

Antes de ejecutar Spec Kit, seleccionar `specs/003-fichas-adquisiciones` siguiendo [el índice SDD](../../docs/sdd/README.md#seleccionar-el-paquete-correcto-en-spec-kit) y verificar FEATURE_DIR. El chequeo solo verifica documentos; no ejecuta implementación ni pruebas de aceptación.

## Bloque inicial parcial — 2026-11-04

Para reproducir la fase roja sin tocar la base local: `& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisitions inventory.tests.test_permissions.OperatorContractTests --verbosity 1`. Se esperan rutas/comando ausentes y falta de esquema T004, no un PASS. Validaciones de modelos sin aplicar nuevas migraciones: `& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_models --verbosity 1`. Revisar validation.md antes de interpretar los resultados. No ejecutar los pasos funcionales anteriores como si 003 estuviera terminada; las migraciones locales requieren revisión previa de Alex.

Tras la corrección técnica, la aceptación anterior sigue roja (14 métodos, 17 fallos contando subtests, sin errores inesperados). Las pruebas de modelos incluyen predicados CHECK mediante SELECT, sin esquema nuevo; no confundirlas con constraints instalados. El estado vigente y la selección de regresión 65/65 constan en validation.md.

## Revisar expansión T004 sin aplicarla localmente

La migración preparada es 0004_acquisition_expansion. Para verificarla solo en el clúster temporal: `& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py inventory.tests.test_acquisition_schema --verbosity 1`. Resultado registrado: 10/10. Leer validation.md e integration-notes.md para límites y reversión bloqueada; no ejecutar migrate local ni asumir que T004 está completa. La aceptación separada ahora llega a servicios/rutas ausentes, no a un bloqueo de tablas.

## Verificar T007 solo con PostgreSQL temporal

`& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 1` ejecuta la suite completa: evidencia actual 118/118. La selección nominal de aceptación de validation.md devuelve 13/13. Las pruebas crean Operadores y catálogos ficticios únicamente en el clúster temporal; no ejecutar create_operator/migrate contra la instalación local sin la revisión correspondiente. Las rutas bloqueadas devuelven 409/503 y el frontend aún no completa los nuevos campos de alta/gestión Operador.


## Verificar compras T008–T010 sin tocar la base local

Automatizado:

~~~powershell
& ./backend/.venv/Scripts/python.exe backend/tools/test_postgres.py --verbosity 1
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
~~~

Evidencia actual: 124/124 backend; 34/34 frontend; build PASS.

Recorrido UI preparado, no ejecutado manualmente contra la instalación local: entrar como Gestor, Registrar activo, guardar factura textual o cargar su identificador, elegir facultad/importe y confirmar fecha o motivo; registrar un activo y repetir con la misma factura para el siguiente. El documento/lock se conservan al cerrar y reabrir dentro de la sesión. Consultar factura permite contrastar lo confirmado; un rechazo conserva datos y no crea otra factura. No borrar factura/activos para reiniciar.

No iniciar este recorrido con la base local sin revisión/aplicación autorizada del esquema y catálogo real. El camino de items sobre activos ya existentes y los pendientes anteriores siguen documentados en integration-notes.md. No interpretar test/build como migración, validación manual ni cierre total de T008–T010.

## Donaciones T011–T013 — actualización 2026-11-04

Automatizado y aislado: ejecutar backend/tools/test_postgres.py inventory.tests.test_donations --verbosity 0; suite completa con backend/tools/test_postgres.py --verbosity 0. Desde frontend: npm test -- --run y npm run build. Resultados finales en validation.md.

Recorrido preparado, NO ejecutado manualmente contra PostgreSQL local: Gestor → Registrar donación → tipo/referencia → Guardar respaldo → registrar varios activos con facultad, valor estimado y fecha/motivo. Alternativamente preparar asociaciones iniciales de fichas existentes sin adquisición, consultando revisión y aportando motivo; se confirman junto al respaldo. Cargar respaldo existente permite continuar altas de activos nuevos; no convierte una compra en donación. Ante conflicto, conservar entrada y revisar la ficha antes de repetir.

No iniciar el recorrido local hasta revisión/aplicación autorizada del esquema y catálogo real. Importes <=0 y fecha documental explícita continúan pending_decision; sin adjuntos, conversión de origen ni integración CSV nueva. Los conteos y límites de apartados anteriores son evidencia histórica, no estado actual.


</details>
