# Validación del incremento de semana 3

Base de integración: `develop` en `5972913d14082bc4be4e39af28c58e339cb71f33`. El trabajo de semana 3 está preparado localmente sobre una rama derivada de esa revisión.

| Comprobación | Resultado | Alcance |
| --- | --- | --- |
| Suite backend | 284 pruebas aprobadas | PostgreSQL temporal, incluido el recorrido HTTP completo |
| API v1 tras la revisión final | 6 pruebas aprobadas | Respuestas, permisos, CSRF, recorrido, compatibilidad de `/api/` y rechazo de PATCH fuera del alcance |
| Esquema OpenAPI 3.1 | Válido | Validador `openapi-spec-validator` 0.7.2; se comprobó el objeto servido |
| Frontend | Suite previa: 83 aprobadas; revisión: 3 pruebas del panel aprobadas | Actualización, paginación, pérdida de acceso y recuperación después de un tiempo de espera agotado; compilación correcta |
| PlantUML | Cuatro fuentes aceptadas y renderizadas | C1, C2, C3 y elementos del código |
| Structurizr | Modelo DSL aceptado | Comando `validate` de Structurizr CLI |

Una primera ejecución del frontend con mayor concurrencia registró cuatro tiempos de espera mientras la interfaz aún cargaba; la repetición con dos procesos aprobó toda la suite. El número total de backend corresponde a la ejecución completa previa a la incorporación del panel visual; después se verificaron los cambios mediante las seis pruebas específicas, la validación OpenAPI y la comprobación en navegador. Una prueba adicional de la revisión final comparó el alta real con fecha desconocida y la ficha de un activo no localizado con sus esquemas JSON; ambas representaciones fueron válidas.

Una comprobación adicional en Chrome usó dos sesiones de gestor, un servidor Django real y PostgreSQL temporal: un gestor registró un activo y el otro lo vio en la tabla sin recargar. La actualización se produjo por la consulta periódica. Primero se aisló la tabla sustituyendo los recursos del CDN y luego se repitió la prueba cargando Swagger UI desde el CDN real; ambas pasaron. Las pruebas de interfaz también comprobaron paginación, limpieza al perder permisos y que los datos se muestran como texto.

El recorrido HTTP real usa un servidor local, credenciales y datos de prueba, una sesión con cookie y token CSRF, y una base PostgreSQL temporal. Registra y consulta un activo, entrega a un custodio y procesa su devolución. No utiliza datos universitarios reales.

## Reproducción

```powershell
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory --verbosity 1
cd frontend
npm.cmd test -- --run --maxWorkers=2
npm.cmd run build
```

El runner requiere PostgreSQL disponible para crear su clúster temporal; las instrucciones completas están en `backend/README.md`. La interfaz Swagger usa un CDN fijado a una versión y necesita conexión para cargar sus recursos; `/api/openapi.json` entrega el esquema localmente. El archivo `openapi-v1.json` es una exportación del mismo objeto; debe regenerarse cuando cambie `backend/inventory/openapi_v1.py`.

La demostración y las pruebas comprueban el subconjunto de v1 descrito, no una migración de todos los módulos del sistema. El historial de PR y las observaciones docentes adicionales se documentarán cuando existan.
