# Encargo al agente de código de Pedro

**Paquete:** 007-qr-activos — QR y apertura autenticada de ficha
**Responsable humano:** Pedro
**Rama exclusiva:** feature/pedro-007-qr-activos
**PR base:** develop. Nunca main. No fusionar automáticamente.

Este archivo es la guía completa que Pedro debe entregar a su agente. Implementa el paquete completo y entrega código, pruebas, evidencia SDD y PR propio. No trabajar en las features asignadas a compañeros. Los nombres de archivos nuevos propuestos deben contrastarse con el árbol real.

## 1. Contexto y alcance

Inventario TI académico UNL, Grupo 5. La base 002 se integró por PR #9 (02cb26c): sesión Django/CSRF de Gestores, activos con código TI automático, registro/listado/ficha/búsqueda/filtros, personas custodias sin cuenta, entregas/devoluciones, cambios de condición, historial y rectificación. Seis paquetes 003–008 completan el alcance acordado. Los Gestores tienen iguales permisos ordinarios; Operador y Revisor poseen solo los permisos definidos en contratos.

Stack existente: Python 3.13, Django 5.2/DRF 3.16/PostgreSQL 17; React 19/TypeScript 7/Vite 8. Leer versiones exactas en requirements.txt y package.json, conservar lockfile y no actualizar todo el stack por costumbre.

Tu alcance es:

QR SVG descargable por activo físico, bajo demanda sin persistir imagen. Enlace canónico con código TI sin PII/tokens. Escaneo externo abre /assets/code/{code}, solicita login y luego ficha. GET /api/assets/by-code/{code}/ resuelve exactamente sin id numérico; no búsqueda parcial. GET /api/assets/{asset_id}/qr.svg solo Gestor, incluso activos No localizado/Baja. PUBLIC_APP_URL, no Host no confiable; retorno interno seguro. Sin fichas públicas ni QR de licencias.

Ejecuta **T001–T010** de `specs/007-qr-activos/tasks.md`. API, pruebas y pantalla web forman parte del encargo. No crear otro proyecto ni reescribir la base. Sin integración universitaria, portal de custodios, imágenes de factura, claves de software, licencias ilimitadas, móvil u otros extras.

## 2. Leer antes de editar

Desde raíz del repo, leer:

1. AGENTS.md aplicables si existen, CONTRIBUTING.md, README.md, backend/README.md y frontend/README.md.
2. .specify/memory/constitution.md: propuesta pendiente de ratificación; no atribuir aprobación al grupo.
3. docs/sdd/alcance-backend-completo.md, decisiones-alcance-backend.md (DBE-001–051), contratos-transversales.md y analisis-cruzado.md.
4. Todos los archivos de `specs/007-qr-activos/`: spec.md, plan.md, research.md, data-model.md, contracts/api.md, contracts/web.md, tasks.md, quickstart.md, validation-plan.md y checklist.
5. Contrato API de 002 y código real backend/inventory/ y frontend/src/; interfaces compartidas de los paquetes proveedores aunque aún no exista su implementación.

Los borradores antiguos son antecedentes, no fuente de verdad. Si hay contradicción, citar archivos/líneas y aclarar antes de decidir funcionalidad. Preguntar a Pedro sobre dudas funcionales; continuar tareas independientes. No reemplazar una decisión humana por una respuesta inventada de la IA.

## 3. Clonar y crear rama propia

Necesitas Git, acceso al repo, Python 3.13, PostgreSQL 17 con ICU, Node compatible con engines (base 22.23.1), npm y PowerShell/pwsh para los scripts Spec Kit. Verificar versiones.

En una carpeta de trabajo propia:

```sh
git clone https://github.com/SteveJ4ra/inventario-TI-unl.git
cd inventario-TI-unl
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feature/pedro-007-qr-activos
```

Si ya hay una copia/rama, revisar git status y conservar cambios humanos antes de cambiar nada; usar la rama existente si corresponde. No reset --hard, clean, borrado de bases ni force push. Identidad Git real de Pedro; no inventar correo ni firmar por otro alumno.

**Acceso a la base documental:** la coordinación debe publicar la rama docs/sdd-backend-completo o integrarla en develop antes de distribuir estas guías. Si el SDD ya está en develop, omitir el paso siguiente. Si solo existe en la rama documental remota, incorporarla a tu rama recién creada:

```sh
git fetch origin
git merge --no-ff --no-edit origin/docs/sdd-backend-completo
```

Esto incorpora solo la base documental común, no código de otros estudiantes. Declararlo en el PR mientras el PR documental no esté integrado. Si la rama remota tampoco existe, pedir la publicación a Pedro; no usar documentos de origen desconocido. Comprobar que las carpetas SDD ya estén disponibles antes de programar.

## 4. Entorno local desde cero

PowerShell en raíz:

```powershell
python --version
node --version
npm.cmd --version
python -m venv backend/.venv
& .\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend ci
```

Crear venv solo si no existe. Copiar backend/.env.example a backend/.env solo si este último no existe; completar localmente DJANGO_SECRET_KEY y DB_NAME/USER/PASSWORD/HOST/PORT con valores propios. No imprimir ni subir secretos. Preparar rol/base PostgreSQL siguiendo backend/README.md: no recrear DB existente ni conceder CREATEDB al rol de aplicación para correr tests. No hay credenciales compartidas predeterminadas.

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py check
& .\backend\.venv\Scripts\python.exe backend/manage.py migrate
& .\backend\.venv\Scripts\python.exe backend/manage.py create_gestor
```

Estos pasos iniciales usan la base 002 y una base de desarrollo propia. Antes de aplicar migraciones nuevas revisar plan/efectos y datos legados, preservar datos reales. create_gestor solicita usuario/contraseña interactivos; no lo repitas si ya tienes usuario autorizado.

Linux: usar `python3.13 -m venv backend/.venv`, `backend/.venv/bin/python` y `npm`; los scripts incluidos requieren pwsh. Windows: npm.cmd evita bloqueo de npm.ps1 sin cambiar políticas de ejecución del sistema.

Para recorrido web, abrir dos terminales:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

```powershell
npm.cmd --prefix frontend run dev
```

Abrir http://127.0.0.1:5173/. ECONNREFUSED hacia 8000 significa backend sin escuchar; no se soluciona elevando permisos de PowerShell. No detener procesos ajenos si un puerto está ocupado.

## 5. Selección explícita y ciclo SDD

Spec Kit ya está incluido. No reinicializarlo, reemplazar Copilot/Codex ni regenerar Constitución. En la sesión PowerShell/pwsh del agente:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/007-qr-activos'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

FEATURE_DIR debe terminar exactamente en 007-qr-activos. El marcador local puede apuntar a 002: cambiar de rama no selecciona feature. Mantener estas variables en la sesión de los comandos. No sobrescribir el marcador compartido ni ejecutar tareas de otra carpeta.

Ciclo: releer Specify/Clarify existentes → contrastar Plan/modelo/contratos → Analyze → Implement por bloques → Validate. Si el agente soporta skills locales speckit-analyze/speckit-implement, leer sus SKILL.md y seguirlos; si no, efectuar el mismo proceso directamente sobre archivos. No fingir comandos de skills ejecutados ni volver a Specify para ampliar alcance.

Antes de cada bloque indicar qué Txxx/FR implementa. Marcar [x] únicamente tareas completas con evidencia; parcial/bloqueada conserva [ ] y explicación en implementation.md. Checklist de requisitos no equivale a test aprobado.

## 6. Avanzar sin esperar compañeros

**Dependencias:** 002 real. No necesita Facultad, mantenimiento ni licencias.

Implementa con 002. Si no existen No localizado/Baja, no añadas lifecycle/decommission: prueba resolución/autorización de ficha genérica y deja escenario de esos estados como integración con 004/005. La ruta no debe filtrar por Disponible, para seguir funcionando cuando lleguen esos estados.

Contrato que entregas/consumes: endpoint SVG, resolución exacta por TI y enlace profundo autenticado. Sin nuevas tablas de activo/licencias.

No permanecer esperando al compañero para desarrollar lógica, contratos, UI, pruebas aisladas y abrir PR. Los fakes/mocks se permiten en tests; nunca como proveedor de producción que devuelve éxito ficticio. Si falta un modelo proveedor, Django puede no arrancar/migrar: registrar ese error real en vez de quitar la FK o relajar restricciones.

Entregar el PR propio incluso con integración pendiente; usar Draft cuando esa falta impide verificación integral. El cuerpo debe distinguir implementado, probado aisladamente, probado con proveedores reales y pendiente. No declarar la feature íntegramente validada ni forzar un merge que deje develop roto. La coordinación ordenará integración de dependencias y hará la auditoría final conjunta después; esto no bloquea abrir tu PR.

No fusionar ramas de implementación ajenas por iniciativa propia, ni crear tablas duplicadas de sus modelos. Cuando proveedores estén en develop, hacer fetch y merge normal de origin/develop en tu rama, resolver conflictos propios, ejecutar regresiones y actualizar evidencia. No fuerza de historial rutinaria.

## 7. Diseño y archivos compartidos

Superficie prevista: backend/inventory servicio QR, views.py, urls.py, requirements.txt (Segno) y tests específicos nuevos. frontend/src/App.tsx, api.ts y ficha real (comprobar Inventory.tsx antes de crear una ficha duplicada).

Puntos de riesgo del paquete:

QR es identificador, no credencial. Sesión/permiso ausente devuelve 403. Fijar versión compatible de Segno sin actualizar todo el stack. Validar rutas/códigos y no redirigir externamente. PUBLIC_APP_URL debe ser accesible desde dispositivo escáner: 127.0.0.1 en teléfono es ese teléfono; no afirmar escaneo móvil si solo se probó PC. Cambiar URL puede invalidar etiquetas ya impresas; documentarlo.

Aplicar siempre contratos-transversales: backend autoriza; no confiar en botones, autores/timestamps/snapshots del cliente. Transacciones y expected_revision; eventos históricos inmutables y estado actual como proyección. Errores de sesión 403 como 002. No historial borrado ni sobreescrito.

Compartimos models.py, services.py, rutas, sesión, App.tsx e historial. Cambiar lo mínimo y preservar 002; no reorganizar todo el repo. Migraciones dependen de nombres reales existentes, no de números futuros del compañero. Colisiones de ramas se resuelven en integración sin borrar historia ni renombrar migraciones ya aplicadas. Las rutas de archivos nuevos son propuestas: inspeccionar antes de crear componentes duplicados.

## 8. Validación real

Leer validation-plan.md y quickstart. Añadir pruebas relevantes de permisos, entradas inválidas, estado HTTP/cuerpo, ausencia de escrituras en rechazo, concurrencia y auditoría, además de regresión de 002. PostgreSQL real para integridad/carreras; no SQLite como atajo.

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py
& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
& .\backend\.venv\Scripts\python.exe -m pip check
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
git diff --check
```

Runner aislado existente: PostgreSQL temporal privado, credenciales efímeras y limpieza solo de sus archivos, sin tocar .env/DB local ni permisos del rol. PG_BIN permite indicar binarios; en Linux usuario normal, no root. Prueba focalizada orientativa: Seleccionar el nombre real del módulo nuevo de pruebas y pasarlo al runner; no asumir un módulo inexistente.

No copiar conteos/resultados históricos de 002 como si fueran propios. Si un test falla por tu cambio, corregirlo. Si depende de proveedor ausente, registrar comando/error y escenario pendiente; no silenciar suites, simular aprobación o marcar skip sin causa. Si falta entorno, indicar NO EJECUTADO/BLOQUEADO y continuar lo verificable.

## 9. Evidencias de Implement y Validate

Implement produce código, no solo un Markdown. Después del trabajo real crear/actualizar dentro de `specs/007-qr-activos/`:

- **implementation.md:** fecha/entorno; Txxx y FR; código/endpoints/migraciones entregados; decisiones técnicas justificadas; ejecución; participación de IA; pendientes y revisión humana real/pendiente.
- **validation.md:** comando exacto por caso, fecha/versiones, FR/SC, resultado y evidencia relevante. Estados PASS/FAIL/NO EJECUTADO/DEPENDENCIA NO INTEGRADA. Diferenciar mocks de DB/servicios reales; API/permisos, DB, frontend/build y manual si efectivamente ejecutado. No datos privados ni resultados por anticipado.
- **integration-notes.md:** commit base (`git rev-parse origin/develop`), proveedores presentes/ausentes, contratos/adaptadores, archivos comunes, grafo/estado de migraciones, casos de regresión y acciones concretas pendientes de auditoría. Si no hay bloqueo, decirlo con evidencia.

Actualizar tasks y quickstart según lo ejecutado; no recortar validation-plan para esconder faltantes. Cambios funcionales se aclaran con Pedro; los técnicos se justifican. No marcar ratificación de Constitución por iniciativa de IA. No crear estos informes afirmando éxito antes de programar/probar.

## 10. Commits y PR hacia develop

Revisar diff/status. No subir .env, venv, node_modules, DB, capturas privadas ni temporales. Commits propios y revisables con feat/test/fix/docs. Comandos (sustituir el marcador de rutas por archivos reales revisados):

```sh
git status
git diff --check
git add <rutas-revisadas>
git commit -m "feat: implementar 007-qr-activos"
git push -u origin feature/pedro-007-qr-activos
```

Este encargo contempla publicar la rama propia y crear su PR cuando el acceso del alumno esté configurado. Si falta autenticación, pedirla al humano; no buscar tokens ajenos. Crear el cuerpo en `specs/007-qr-activos/pr-description.md` con alcance, links SDD, FR/tareas completadas, cambios API/migraciones, pruebas reales, límites y dependencias pendientes; sin copiar conversación.

Con gh disponible/autenticado:

```sh
gh pr create --base develop --head feature/pedro-007-qr-activos --title "feat: 007-qr-activos" --body-file specs/007-qr-activos/pr-description.md
```

Agregar --draft si la validación integral está bloqueada. Sin CLI, usar GitHub con la misma base/head y entregar URL real o motivo verificable si no se pudo abrir. No main, no autoaprobación, no merge automático. Revisión por otro integrante según CONTRIBUTING.md.

## 11. Entrega final al alumno

Entregar a Pedro: resumen de código, rama/commits, URL PR, tareas completas/pendientes, pruebas ejecutadas y sus límites; enlaces implementation.md/validation.md/integration-notes.md. No confundir PR abierto con funcionalidad integrada o auditoría global aprobada. Tras todos los PR se integrarán dependencias y el grupo repetirá validación integral/correcciones de compatibilidad.
