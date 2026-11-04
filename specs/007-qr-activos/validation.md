# Validación — 007: QR de activos

**Fecha:** 2026-11-04  
**Entorno observado:** Windows 11 / PowerShell, PostgreSQL 17.11 con instancia de pruebas temporal, Django 5.2.18, Segno 1.6.6, Vite 8.3.4 y Vitest 5.0.5.  
**Python:** entorno original `backend/.venv` = 3.12.3; entorno adicional `$venv313` = 3.13.17 (comprobación por consola). El usuario mostró corrida posterior de 55/55 pruebas, pero la captura final no muestra qué ejecutable inició esa corrida.  
**Fuente de evidencia:** salidas y capturas de consola/navegador aportadas por el alumno durante la sesión; no se publican contraseñas, bases ni capturas privadas.

> Estados: **PASS** = comprobado; **NO EJECUTADO** = falta prueba; **DEPENDENCIA NO INTEGRADA** = no disponible aún; **FAIL** = prueba ejecutada y fallida. Una compilación exitosa no equivale a validar todo el flujo del QR.

## 1. Verificación automatizada

| ID / criterio | Comando ejecutado (desde la raíz del repositorio) | Resultado y evidencia | Estado |
|---|---|---|---|
| QR-API / FR-001, FR-002, FR-004–FR-007 | `& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory.test_qr_assets --verbosity 2` | `Ran 10 tests in 1.096s` / `OK`. Suite nueva incluye acceso sin sesión, usuario no Gestor, SVG, URL canónica, Host alternativo, código exacto, no encontrado e ID inexistente. | PASS |
| Regresión backend / base 002 y QR | `& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py --verbosity 2` | `Ran 55 tests in 3.882s` / `OK`. **Incluye** los 10 anteriores; no sumarlos como 65 casos diferentes. PostgreSQL temporal y eliminación automática de `test_postgres`. | PASS |
| Regresión frontend con tests QR | `npm.cmd --prefix frontend test -- --run` | Corrida posterior: `9 test files passed`, `25 tests passed`; incluye 5 pruebas en `frontend/src/tests/qr.test.tsx`. Los 20 casos previos también pasaron. | PASS |
| Compilación TypeScript + Vite | `npm.cmd --prefix frontend run build` | Compilación satisfactoria; `24 modules transformed` y `built in 229ms` en una ejecución documentada. | PASS |
| Migraciones | `& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run` | `No changes detected`. | PASS |
| Dependencias | `& .\backend\.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` | PASS |
| Formato básico Git | `git diff --check` | Sin salida de errores. | PASS |
| Frontend QR específico / FR-003, SC-002 | `npm.cmd --prefix frontend test -- --run` (archivo `src/tests/qr.test.tsx`) | 5/5 PASS; la consola identifica el caso “QR sin sesión: solicita login y luego abre la misma ficha”. No atribuir pruebas no visibles a esos cinco casos sin revisar su contenido. | PASS |

**Método de pruebas:** las suites Django se ejecutaron con el runner PostgreSQL temporal del proyecto. El caso de URL canónica observa la llamada al generador real Segno con un *spy*; no sustituye la generación productiva por una implementación falsa. Las pruebas web existentes utilizan el entorno de Vitest/JSdom; la navegación web se probó también manualmente.

## 2. Comprobaciones funcionales y manuales

| Caso / SC | Evidencia observada | Estado |
|---|---|---|
| Gestor descarga QR SVG / SC-001, SC-005 | API `200 image/svg+xml`, 1951 bytes en activo local `TI-000001`; navegador descargó `TI-000001.svg` y una segunda copia; SVG visible en PC. | PASS |
| Resolución autorizada por código | API `200` para `TI-000001`; navegador abrió `/assets/code/TI-000001` y mostró «Computadora». | PASS |
| Solicitud no autenticada API / SC-003 | Ambos endpoints devolvieron `403` en cliente Django sin sesión. | PASS |
| Código inexistente y parcial / SC-004 | API devolvió `404` para `TI-999999` y `TI-000`; la web mostró «No se encontró el activo solicitado» y opción de volver. | PASS |
| Retorno tras autenticación / SC-002 | El alumno confirmó manualmente el enlace sin sesión, login y llegada a la ficha `TI-000001`, conservando destino. | PASS (confirmación manual) |
| Cuenta no Gestor / SC-003 | Cubierta en la suite Django focalizada; no consta prueba manual específica en navegador. | PASS (automatizada), NO EJECUTADO (manual) |
| Resistencia a destino/Host externo / SC-004 | Test backend con `HTTP_HOST` alternativo y URL pública `javascript:`/HTTP en producción: todos PASS. No consta prueba de navegación externa en frontend. | PASS (backend), NO EJECUTADO (frontend) |
| Escaneo desde otro dispositivo / SC-005 | El teléfono reconoció/decodificó el QR correctamente. No pudo abrir la web porque `127.0.0.1` es local a cada dispositivo. La apertura desde otra red/dispositivo está pendiente hasta configurar una URL accesible. | PASS (reconocimiento) / PENDIENTE (apertura remota) |
| Impresión y lectura del SVG a diversos tamaños / SC-005 | El alumno indicó que las demás comprobaciones manuales cumplen, incluida legibilidad. No constan todavía medidas exactas de etiquetas, dispositivo ni captura de los tamaños impresos; registrar esos detalles antes de concluir aceptación formal. | PASS declarado por alumno / EVIDENCIA INCOMPLETA |
| Activos No localizado / Baja / FR-008 | Según el encargo, estos estados pueden depender de los paquetes 004/005; no se dispone de evidencia de su integración. | DEPENDENCIA NO INTEGRADA |
| Licencias / FR-007 | El encargo excluye QR de licencias; no consta prueba con modelos de licencias de otros paquetes. | DEPENDENCIA NO INTEGRADA |

## 3. Pasos de aceptación que aún deben ejecutarse

1. **Realizado:** el alumno confirmó que una ventana sin sesión muestra login y luego abre `TI-000001`. Mantener la ruta como destino interno; no introducir mecanismos de redirección externa.
2. **Realizado parcialmente según alcance probado:** `src/tests/qr.test.tsx` aportó cinco pruebas PASS y la suite completa pasó 25/25. Antes del PR, revisar que los casos presentes coincidan con todos los criterios exigidos por `validation-plan.md` (no presumir casos que no se muestran en consola).
3. **Pendiente de coordinación:** acordar URL HTTPS canónica de despliegue, accesible desde el teléfono; cambiar `PUBLIC_APP_URL` y regenerar las etiquetas finales.
4. **Pendiente de detalle documental:** el alumno confirma legibilidad del QR; consignar medidas de los dos tamaños impresos y el lector usado, o declarar que esa evidencia aún no está disponible.
5. Repetir pruebas de integración con los estados No localizado/Baja cuando sus proveedores estén disponibles. Ejecutar regresión después de resolver conflictos de integración.
6. Adjuntar al PR capturas **sin secretos** de consola/build, descargas, login, ficha y errores de búsqueda. Anotar comandos y versiones exactas.

## 4. Interpretación de resultados

Las pruebas realizadas soportan el backend QR, el flujo de login y las 5 pruebas específicas del frontend. **No autorizan aceptación integral** hasta cerrar URL de despliegue, detalle reproducible de impresión y revisión de integración de proveedores. El comando `makemigrations` solo constata que no hay cambios de modelos pendientes; no sustituye un examen de migraciones de futuros proveedores.
