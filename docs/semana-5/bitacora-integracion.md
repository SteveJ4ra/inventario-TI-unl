# Bitácora de integración y decisiones

Las entradas corresponden a cambios y comprobaciones verificables del repositorio y del entorno local. No representan sesiones de clase adicionales ni una aprobación docente distinta de las observaciones comunicadas.

| Etapa | Hecho o problema | Decisión/corrección | Evidencia |
| --- | --- | --- | --- |
| Base SDD | Reglas del inventario aclaradas antes de ampliar módulos | Mantener decisiones y especificaciones 002-008 | docs/sdd/ y specs/ |
| Integración funcional | Aportes de los seis módulos incorporados en develop | Conservar autoría y revisar compatibilidad, transacciones y dependencias | PR #14-18 y #20; historial Git |
| Semana 2 | Requisitos y filtros necesitaban orden común | Dossier compartido, catálogo funcional y simplificación | PR #21, #22 y #23 |
| Semana 3 | Se solicitó una página de API visual y actualización de otros gestores | /api/docs/, Swagger y consultas periódicas protegidas; mantener /api/ | PR #24, #25 y #26 |
| Semana 4 | Límite de acceso y duración de sesión requerían controles explícitos | Cinco fallos por cuenta/IP, treinta minutos absolutos y no-store | PR #27, #28 y #29; base 435b0e0 |
| Semana 5: alcance | Se confirmó Compose local y la misma fecha académica; sin observación docente adicional | Backend y PostgreSQL; demostrar URL localhost y reproducibilidad | ADR-0501 y plan S5 |
| Arranque de prueba | Secretos con CRLF provocaron error de autenticación entre Windows y Linux | Escritura LF explícita y repetición sobre el volumen de prueba recién creado | init correcto, rol operativo autenticado |
| Arranque sin root | collectstatic no podía escribir en /app/staticfiles | Dar permiso únicamente al directorio estático del UID 10001 | CSS HTTP 200 y UID comprobado |
| Contenedor de pruebas | Dos pruebas históricas no encontraban faculty_contract.py.txt | Conservar estructura backend/specs e incluir la plantilla | Suite completa sin omitirlas |
| Recorrido HTTP | QR local devolvía 500 al exigir HTTPS con DEBUG=false | Excepción explícita para loopback y pruebas que mantienen el rechazo externo | Dos regresiones y QR SVG 200 |
| Cobertura de ejecución | inventory no incorporaba por sí solo las pruebas contractuales separadas | Añadir contract_tests y ejecutar dos suites aisladas | 333 pruebas Django, 21 políticas y 16 importación |
| Persistencia | Se necesitaba comprobar el volumen más allá de un simple restart | down sin --volumes y nuevo up --wait | Dos activos antes/después |
| Seguridad de transporte | check --deploy reportó cuatro advertencias HTTPS | Mantenerlas visibles y limitar el entorno a loopback HTTP | W004, W008, W012 y W016; no se declara TLS público |
| Cierre documental | Las fuentes históricas mostraban conteos/etapas distintas | README actual, catálogo de 59 rutas y 104 FR trazados | Dossier y evidencia-validacion.json |

Los PR citados son registros reales de semanas anteriores. Los archivos de semana 5 se preparan localmente en feature/semana-5-integracion y se publican mediante los aportes autorizados hacia develop; no se asignan números de PR inexistentes. La incorporación posterior se registra conservando estas comprobaciones como evidencia local.

Las tareas históricas de los módulos se conservan como registro de su etapa. El estado integrado se consulta en el dossier, no deduciendo una aprobación actual de un checklist antiguo.
