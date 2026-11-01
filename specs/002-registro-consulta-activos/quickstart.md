# Guía de ejecución y validación

**Estado:** incremento implementado y validado localmente. Resultados reales y límites: [validation.md](validation.md). Preparación completa: [backend/README.md](../../backend/README.md) y [frontend/README.md](../../frontend/README.md).

## Preparación del entorno

Desde la raíz del repositorio, utilizar Python 3.13, PostgreSQL 17, Node 22.23.1 o compatible con las dependencias fijadas y npm. Conservar el .env privado existente; una instalación nueva usa backend/.env.example y credenciales propias. Nunca sobrescribir un .env ya configurado sin revisarlo.

En una instalación configurada, PowerShell:

```powershell
& .\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
& .\backend\.venv\Scripts\python.exe backend/manage.py check
& .\backend\.venv\Scripts\python.exe backend/manage.py migrate
& .\backend\.venv\Scripts\python.exe backend/manage.py create_gestor
npm.cmd --prefix frontend ci
```

`create_gestor` pedirá nombre de usuario y contraseña de forma interactiva; creará/asignará el grupo Gestores sin publicar credenciales. Preparar un segundo gestor del mismo modo para verificar colaboración. No usar datos personales reales en las demostraciones.

Dos terminales:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

Abrir http://127.0.0.1:5173/. Proxy de desarrollo para /api hacia 127.0.0.1:8000; configurar únicamente ese origen local de confianza CSRF. Si los puertos están ocupados, elegir libres y ajustar el proxy; no detener procesos ajenos. Login/CSRF según [contrato API](contracts/api.md). Estos servidores son de desarrollo, sin publicación pública.

En Linux se usa backend/.venv/bin/python en lugar de Scripts/python.exe. No se necesita activar el venv si se invoca su Python directamente.

## Pruebas automatizadas

El usuario actual de aplicación no tiene CREATEDB y no se cambió ese permiso. Ejecutar el runner aislado, que utiliza PostgreSQL 17 con ICU:

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py
```

El runner crea un directorio temporal nuevo, escucha solo en loopback con credenciales efímeras, pasa las variables al proceso de pruebas sin modificar backend/.env y detiene/elimina únicamente su entorno. PG_BIN permite indicar los binarios PostgreSQL; en Linux ejecutarlo como usuario normal, no root.

Con variables de un entorno de pruebas ya preparado, el comando subyacente será:

```powershell
& .\backend\.venv\Scripts\python.exe backend/manage.py test inventory --verbosity 2
& .\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
```

Resultados locales: 28 pruebas backend y 17 frontend correctas; build y comprobación de migraciones correctos. La suite cubre restricciones, permisos, CSRF, contratos, snapshots/rollback, revisión obsoleta y carreras con conexiones independientes. Ver [plan.md](plan.md) y [research.md](research.md).

## Recorrido de aceptación con datos ficticios

| Paso | Acción | Resultado / referencia |
|---|---|---|
| 1 | Intentar consultar sin sesión; probar usuario sin grupo. | Acceso denegado en API y web; SC-013. |
| 2 | Entrar como gestor A y crear portátil operativo, marca Ejemplo, modelo A1, serie LAB-001, ubicación Laboratorio 1. | Código TI automático, Disponible, sin custodio; SC-001/004/007. |
| 3 | Intentar alta equivalente con espacios y mayúsculas; crear otro con serie LAB001. | Rechazar duplicado; caracteres internos distinguen la otra serie; SC-002/003. |
| 4 | Crear persona ficticia con correo válido y dependencia opcional; repetir correo con mayúsculas. | Primera aceptada sin crear cuenta, segunda rechazada; SC-011. |
| 5 | Entregar el activo a esa persona y destino Aula 2. | Asignado, custodio y ubicación nuevos, autor A y evento; SC-006/008/012. |
| 6 | Entrar como gestor B, consultar y devolver como Averiado a Laboratorio 1. | Iguales permisos; Disponible sin custodio, antecedente conservado y autor B; SC-006/007/013. |
| 7 | Intentar nueva entrega y otra devolución sin custodia. | Rechazar ambas sin cambios; SC-007/014. |
| 8 | Cambiar Averiado → En reparación → Operativo con motivos. | Eventos de cambio con autor, fecha y condiciones; ahora permite entrega; SC-010. |
| 9 | Rectificar el último cambio con motivo. | Original conservado y snapshot anterior restaurado; SC-009/016. |
| 10 | Intentar rectificar otra vez, rectificar la rectificación o un evento antiguo. | Rechazar sin cambiar ficha/historial válido; SC-014. |
| 11 | Registrar por separado el cambio correcto y filtrar/buscar datos conocidos. | Evento nuevo; AND entre filtros y búsqueda, ficha correcta; SC-005/009. |
| 12 | Desde dos sesiones preparar la misma revisión y competir en una entrega. | Solo una entrega aceptada; la otra recibe conflicto; SC-015. |
| 13 | Cerrar sesión y recargar; probar ficha inexistente, lista vacía y error de campo. | Sin datos privados tras logout; mensajes comprobables según historias 1/5/6. |

La suite automatizada comprobará también rectificar una entrega y una devolución: restaurar respectivamente el estado anterior sin custodia o con custodia y la ubicación anterior. El recorrido manual breve no sustituye esos casos.

## Evidencia y revisión

Los resultados reales de tests, build y navegador, el entorno y las limitaciones están registrados en validation.md. Las capturas entregadas usan datos ficticios; los gestores de QA se eliminaron con la base temporal. Mantener trazabilidad FR → aceptación → tarea → prueba. Hacer commits revisables y PR hacia develop con revisión de otro integrante antes de integrar; no afirmar ratificación ni reproducción por un compañero mientras no existan.

## Seleccionar el incremento en Spec Kit

El marcador .specify/feature.json es local y está ignorado por Git. En una copia nueva, antes de usar las skills de Spec Kit, seleccionar explícitamente el directorio activo en la sesión PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "specs/002-registro-consulta-activos"
```

Esto conserva la rama Git feature/registro-consulta-activos; el identificador lógico es 002-registro-consulta-activos. No requiere reinicializar Spec Kit ni reemplazar Copilot por Codex. Los scripts incluidos son PowerShell; en Linux requieren pwsh. Esta configuración de Spec Kit es independiente de ejecutar la aplicación con Python y npm.
