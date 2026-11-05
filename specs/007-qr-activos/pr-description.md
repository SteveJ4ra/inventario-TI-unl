# feat: 007-qr-activos

## Alcance implementado

- Generación bajo demanda de QR **SVG** por activo físico con Segno 1.6.6.
- URL canónica configurable mediante `PUBLIC_APP_URL`, con código TI y sin datos personales ni ID numérico.
- Endpoint Gestor `GET /api/assets/{asset_id}/qr.svg` y resolución exacta `GET /api/assets/by-code/{code}/`.
- Enlace profundo de React `/assets/code/{code}` y botón de descarga desde ficha existente.
- Uso de autorización y sesión de la base 002; ninguna tabla ni migración nueva del paquete QR.

## Trazabilidad y documentos

- Especificación: `specs/007-qr-activos/spec.md`
- Contratos: `specs/007-qr-activos/contracts/api.md`, `contracts/web.md`
- Plan y tareas: `specs/007-qr-activos/plan.md`, `tasks.md`
- Evidencias: `implementation.md`, `validation.md`, `integration-notes.md`
- FR principales: FR-001–FR-008; validación de aceptación completa **pendiente** según el detalle adjunto.

## Pruebas ejecutadas (2026-11-04)

| Comprobación | Resultado |
|---|---|
| QR backend: `backend/tools/test_postgres.py inventory.test_qr_assets --verbosity 2` | **10/10 PASS** |
| Suite general backend: `backend/tools/test_postgres.py --verbosity 2` | **55/55 PASS** (incluye los 10 QR) |
| Frontend: `npm.cmd --prefix frontend test -- --run` | **25/25 PASS** (incluye 5 pruebas QR) |
| `npm.cmd --prefix frontend run build` | **PASS** |
| `manage.py makemigrations --check --dry-run` | **PASS — No changes detected** |
| `python -m pip check` y `git diff --check` | **PASS** |
| Manual: QR SVG, descarga Edge, enlace con sesión, código inexistente, retorno tras login | **PASS** según comprobación del alumno |

## Pendientes y límites explícitos

- Confirmar dirección `PUBLIC_APP_URL` **HTTPS** de despliegue; localmente se usa `127.0.0.1:5173`, que no es accesible por un teléfono remoto.
- El caso sin sesión → login → ficha fue confirmado por el alumno y se agregaron 5 tests frontend QR. Mantener evidencia precisa de sus escenarios.
- El teléfono reconoció el QR y el alumno confirma legibilidad. Falta registrar medidas/lector de impresión y comprobar apertura desde URL HTTPS accesible; T009 continúa abierto a aceptación formal.
- Actualizar y revisar la evidencia final T010. `backend/.env.example` ya documenta `PUBLIC_APP_URL`; asegurarse de incluir el cambio en Git.
- Probar con estados No localizado/Baja cuando paquetes 004/005 estén integrados.
- El entorno original usa Python 3.12.3 y se comprobó uno alterno con Python 3.13.17. La revisión humana/compatibilidad SDD siguen pendientes.

## Dependencias e integración

Se integra con el proveedor real 002 (Gestores/Asset/ficha/historial). No se fusionaron otras ramas de implementación. Existe riesgo de conflictos en `views.py`, `urls.py` y `App.tsx`; verificar al integrar. La documentación completa está en `integration-notes.md`.

## Revisión solicitada

Revisar endpoints y permisos, destino interno tras login, ausencia de PII, pruebas QR y regresiones, y comprobar conflictos en archivos compartidos. **No autoaprobar ni fusionar**. Si la revisión de integración/aceptación no puede terminarse aún, abrir este PR como **Draft** con base `develop`.
