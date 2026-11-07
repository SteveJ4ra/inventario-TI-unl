# Plan SDD del incremento de integración y despliegue

## Necesidad y restricciones

Hacer reproducible el backend acordado sin ampliar funcionalidades. Usar Docker Compose local, evidenciar funcionamiento y mantener los criterios de seguridad y trazabilidad. La APE conserva fecha 06/11/2026, 07:30-09:30, aula. No se recibió otra retroalimentación docente final.

## Especificación y aclaraciones confirmadas

| ID | Criterio de aceptación | Evidencia |
| --- | --- | --- |
| S5-01 | Construir la imagen sin archivos secretos ni configuración privada | Dockerfile, .dockerignore y comprobación de imagen |
| S5-02 | Arrancar db, migración y web en orden; servir la API en loopback con DEBUG=false y usuario sin root | Compose, perfil settings_deploy y recorrido HTTP |
| S5-03 | Ejecutar la suite en otra base, sin privilegios adicionales sobre la base de aplicación | Perfil test, test_runner.py y evidencia 333 pruebas |
| S5-04 | Demostrar registro, consulta, entrega/devolución, historial y rechazos, manteniendo sesión/CSRF | deploy/smoke.py y 30 respuestas HTTP |
| S5-05 | Conservar información al recrear servicios sin borrar el volumen | Evidencia de persistencia: dos activos antes/después |
| S5-06 | Organizar especificaciones, arquitectura, contratos, pruebas, operación y decisiones | Dossier, matriz, catálogo API, ADR y bitácora |
| S5-07 | Admitir el QR local sin permitir HTTP externo en el perfil desplegado | Permiso explícito QR_ALLOW_LOCAL_HTTP y dos pruebas de regresión |

La constitución continúa con el estado documental de propuesta que conserva su fuente; se aplican sus principios de trazabilidad, integridad, seguridad, verificabilidad y alcance controlado. No se atribuye una ratificación grupal que no figure en sus registros.

## Diseño y análisis

Django/DRF y PostgreSQL conservan sus módulos y contratos. Un perfil de settings añade lectura de secretos, hosts, estáticos y seguridad de transporte. Compose incluye servicios de arranque y prueba independientes. ADR-0501 justifica alternativas y límites. La matriz incluye todos los FR de las especificaciones 002-008, con un alcance expresamente backend y evidencia asociada verificable.

Se detectaron y corrigieron cuatro problemas de integración: CRLF en secretos, permisos de staticfiles con usuario sin root, ausencia de la plantilla histórica en la imagen de pruebas y rechazo de QR HTTP de loopback con DEBUG=false. No se cambió DEBUG a true ni se otorgó SUPERUSER al rol operativo para resolverlos.

## Tareas y validación local

- [x] Revisar guías de AA, ACD y APE 5 y confirmar despliegue local y datos académicos.
- [x] Preparar imagen, Compose, secretos, rol limitado y volumen persistente.
- [x] Implementar perfil desplegado, arranque explícito y estáticos.
- [x] Incorporar seis pruebas nuevas de configuración y QR.
- [x] Ejecutar suite de 333 pruebas, 30 comprobaciones HTTP y chequeo de migraciones.
- [x] Comprobar persistencia y documentar advertencias HTTPS del perfil local.
- [x] Organizar dossier, estándares, contratos, bitácora y trazabilidad.

La publicación de este incremento sigue el flujo de ramas y PR hacia develop autorizado por Steven; la validación local y la integración publicada son evidencias distintas. La guía de cada paquete delimita los archivos y no autoriza por sí sola abrir ni fusionar un PR.
