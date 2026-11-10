# Implementación — 007: QR de activos físicos

**Proyecto:** Inventario TI Académico UNL — Grupo 5  
**Responsable:** Pedro  
**Fecha de registro:** 2026-11-04  
**Rama de trabajo:** `feature/pedro-007-qr-activos`  
**Referencia local de `origin/develop` al consultar:** `4247cc8998ed810fdb6462941d85f3324260a2ec`  
**Estado:** implementación principal funcional en desarrollo local; aceptación integral pendiente.

## 1. Objetivo y alcance

Se añadió la descarga de QR SVG por activo físico y la apertura de su ficha mediante un enlace interno cuyo identificador es el código TI, sin exponer datos personales en el QR. No se habilitaron fichas públicas ni se conceden permisos por poseer el QR. Reutiliza el backend Django, la sesión Gestor y la ficha React existentes de la base 002. Los criterios y límites están definidos en `spec.md`, `plan.md`, `contracts/api.md` y `contracts/web.md` de este paquete.

## 2. Archivos de código implementados

| Archivo | Cambio y responsabilidad |
|---|---|
| `backend/config/settings.py` | Lectura de `PUBLIC_APP_URL` desde el entorno. |
| `backend/requirements.txt` | Dependencia `segno==1.6.6` fijada. |
| `backend/inventory/qr_urls.py` (nuevo) | Construye la URL canónica a partir de `PUBLIC_APP_URL` y del código TI; valida esquema y evita usar `Host` entrante. |
| `backend/inventory/views.py` | Vista autenticada de SVG en memoria y vista para resolución exacta por código TI. |
| `backend/inventory/urls.py` | Rutas para QR y búsqueda por código. |
| `backend/inventory/test_qr_assets.py` (nuevo) | Diez casos de seguridad y comportamiento QR. |
| `frontend/src/App.tsx` | Botón de descarga SVG y ruta `/assets/code/{code}`, manteniendo el destino local en la barra de direcciones mientras se presenta el login. |

**Configuración local:** `backend/.env` contiene `PUBLIC_APP_URL=http://127.0.0.1:5173`; es privado y **no se debe añadir a Git**. La comprobación de `git status --short` no mostró cambios en `backend/.env.example`; `backend/.env.example` ya incluye la variable de ejemplo; Git detectó el cambio local. Verificar que se incorpore al commit.

## 3. Contratos entregados

| Contrato | Comportamiento |
|---|---|
| `GET /api/assets/{asset_id}/qr.svg` | Solo Gestor; `200 image/svg+xml` + descarga; `403` sin autorización; `404` si no existe. SVG generado bajo demanda. |
| `GET /api/assets/by-code/{code}/` | Solo Gestor; devuelve ficha del activo correspondiente al código exacto; `403` o `404` en rechazo. |
| `/assets/code/{code}` | Ruta del frontend que conserva el código al solicitar autenticación y, una vez habilitada la sesión, consulta la API. |

El QR para el activo de demostración `TI-000001` codifica `http://127.0.0.1:5173/assets/code/TI-000001` en el entorno local. El SVG no incorpora el identificador numérico ni información del custodio. Esta dirección **no sirve para un teléfono fuera del propio equipo** y no es apta para etiquetas definitivas.

## 4. Decisiones técnicas y justificación

- **Segno 1.6.6**, con versión fijada para instalación reproducible; licencia **BSD** indicada por PyPI: https://pypi.org/project/segno/1.6.6/ . No se actualizó indiscriminadamente el stack.
- **SVG en memoria** mediante `BytesIO` y `HttpResponse` para evitar tablas o archivos permanentes de QR; respuesta con `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`.
- **URL canónica** configurada mediante `PUBLIC_APP_URL`, no derivada del encabezado `Host`, sin credenciales ni tokens.
- **Backend autoriza**; ocultar/mostrar el botón en frontend no constituye el control de acceso.
- **Sin migraciones nuevas:** los endpoints consumen el modelo `Asset` ya existente. `makemigrations --check --dry-run` devolvió `No changes detected`.
- **Rutas internas**, sin aceptar `next` con una URL externa. La aceptación post-login requiere completar las pruebas específicas detalladas en `validation.md`.

## 5. Trazabilidad tareas/requisitos

| Tarea | FR/SC relacionados | Situación documentada |
|---|---|---|
| T001 | FR-006 | Configuración local comprobada; falta URL HTTPS de despliegue y revisión de `.env.example`. |
| T002 | FR-002, FR-007 | Segno 1.6.6 instalado, fijado y licencia documentada. |
| T003 | FR-001, FR-006 | Generador de URL probado con `TI-000123`. |
| T004 | FR-002, FR-004, FR-005, FR-008 | Endpoints probados con Gestor, ausencia de sesión y códigos inexistentes. |
| T005 | FR-003 / SC-002 | Recorrido sin sesión → login → ficha `TI-000001` confirmado manualmente por el alumno; frontend QR automatizado probado. |
| T006 | FR-002 | Botón visible y descarga real desde el navegador. |
| T007 | FR-003 / SC-002 | Ruta con sesión abre ficha; el alumno confirmó que tras el login se muestra la misma ficha. |
| T008 | FR-001–FR-008 | Diez pruebas QR backend PASS y cinco pruebas nuevas de frontend QR PASS; suites totales backend 55/55 y frontend 25/25. |
| T009 | SC-005 | SVG visible y reconocido por el teléfono; el alumno confirma legibilidad y restantes comprobaciones manuales. No se probó apertura remota por dirección `127.0.0.1`. Registrar medidas específicas de impresión y lector para evidencia reproducible. |
| T010 | Todos | Evidencia actualizada con los resultados posteriores; despliegue HTTPS, detalle de impresión e integración final siguen pendientes. |

## 6. Ejecución en desarrollo

Desde la raíz del repositorio, en **dos terminales**:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
npm.cmd --prefix frontend run dev
```

Acceder a `http://127.0.0.1:5173/`, iniciar sesión como Gestor y abrir la ficha de un activo. Pulsar «Descargar QR (SVG)» o abrir `http://127.0.0.1:5173/assets/code/TI-000001` mientras exista ese activo de prueba.

## 7. Uso de IA, revisión humana y pendientes

La IA se utilizó como apoyo para proponer código de Django/React, guiar la ejecución de comandos y redactar pruebas y documentación. Pedro realizó la instalación local, modificaciones, pruebas por terminal, descarga y comprobaciones visuales mostradas en las capturas compartidas. **No consta todavía una revisión de código completa por otro integrante ni aprobación de integración.**

Pendientes antes de aceptación plena: acordar `PUBLIC_APP_URL` HTTPS real y accesible desde teléfono, documentar medidas y dispositivo usados en impresión/escaneo para evidencia reproducible, probar integración con los estados No localizado/Baja cuando los paquetes proveedores estén presentes, y obtener revisión humana del PR. El login desde enlace QR y las pruebas específicas de frontend ya fueron confirmados. `backend/.env.example` contiene `PUBLIC_APP_URL` y debe añadirse al commit.

**Seguridad:** durante las pruebas se mostró accidentalmente una captura de `.env` con valores sensibles; se recomienda rotar la contraseña expuesta y `DJANGO_SECRET_KEY`, manteniéndolas fuera de commits y capturas. La versión inicial de `backend/.venv` era Python 3.12.3; se instaló un entorno independiente de Python 3.13.17 y se comprobó `pip check`. El alumno mostró una corrida adicional de 55/55 pruebas, aunque el comando exacto de esa corrida no aparece en la captura final.
