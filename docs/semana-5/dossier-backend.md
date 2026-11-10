# Dossier técnico integrado del backend

Proyecto: Inventario TI - Grupo 5 - Unidad 1. Base publicada: develop 435b0e08b9336f4e053ebab53367bbfd8f686e7a. Incremento de semana 5 preparado en feature/semana-5-integracion. El alcance es backend y despliegue local; no se añade una integración institucional ni una aplicación nueva.

## Propósito y alcance confirmado

Controlar activos físicos, su adquisición y custodia, novedades/mantenimiento, pérdida/robo, bajas y licencias finitas, con historial y permisos. El inventario no borra sus antecedentes para corregirlos. Las reglas provienen de decisiones aclaradas y de especificaciones 002-008; no se presenta la propuesta académica como normativa institucional de la universidad.

| Módulo | Necesidad y comportamiento | FR trazados |
| --- | --- | --- |
| 002 | Identificar equipos, consultar, entregar/devolver, cambiar condición y rectificar sin borrar | 23 |
| 003 | Conservar factura o respaldo compartido, valor individual, facultad y edición auditada | 16 |
| 004 | Registrar daños y mantenimiento, conservar estado conocido y recuperar equipos | 16 |
| 005 | Dar de baja sin eliminación y aprobar No localizado con revisor independiente | 17 |
| 006 | Controlar lotes finitos, remanentes y vigencia sin almacenar claves | 12 |
| 007 | Generar QR canónico y resolver el código con acceso autorizado | 8 |
| 008 | Validar/importar activos y licencias, doble confirmación y transacción atómica | 12 |

Total: 104 FR y cinco RNF del dossier base. La matriz completa mantiene requisito, fuente, componente y prueba asociada. Vincular una prueba no demuestra por sí solo que todos los escenarios posibles estén cubiertos. La interacción del cliente se distingue de la funcionalidad API comprobada en esta semana.

## Organización SDD

| Artefacto | Función y ubicación |
| --- | --- |
| Constitución | .specify/memory/constitution.md: principios; conserva el estado de propuesta de la fuente |
| Decisiones y aclaraciones | docs/sdd/ y secciones Clarifications de specs/002-008; no se inventan reglas de negocio al desplegar |
| Especificaciones | spec.md por módulo; actores, historias, FR y aceptación |
| Diseño y contratos | plan.md, data-model.md y contracts/ por módulo; C4/ADR de semanas 3-5 |
| Trabajo y análisis | tasks.md, checklists e integration-notes.md históricos; plan-y-tareas.md registra el incremento S5 |
| Implementación y validación | backend/inventory/, migrations/, implementation.md/validation.md por módulo y evidencia integrada actual |
| Cierre de trazabilidad | matriz-trazabilidad.md/json, catálogo-api.md/json y bitácora-integracion.md |

No se ratifica automáticamente una constitución por ejecutar pruebas ni se marcan como realizadas revisiones humanas no registradas. La evidencia del incremento integrado se usa para interpretar los documentos históricos, preservando su procedencia.

## Arquitectura y responsabilidades

Django/DRF expone vistas y serializadores; los servicios aplican reglas y transacciones; PostgreSQL mantiene restricciones, secuencias, relaciones y auditoría inmutable. Operador, gestor y revisor conservan permisos distintos. El custodio no tiene cuenta de acceso. El adaptador v1 mantiene un contrato de respuesta para el recorrido base y delega en las operaciones ya probadas.

La arquitectura C4 y las decisiones de semana 3 se conservan. El despliegue añade Gunicorn como servidor WSGI, WhiteNoise para estáticos, un trabajo de inicialización anterior al servidor y una base de pruebas separada. El volumen operativo persiste. El diagrama despliegue.puml representa los procesos y límites reales de Compose; ADR-0501 explica alternativas.

## Contratos e interoperabilidad

El catálogo inspeccionado contiene 59 patrones API/documentación. Diez paths OpenAPI describen /api/v1/; los módulos ampliados conservan /api/ y sus contratos Markdown. No se anuncian importación, licencias o bajas como rutas v1 inexistentes.

HTTP indica método, resultado y conflicto; JSON representa los cuerpos, y cada contrato determina tipos y reglas. Las fechas y los decimales se procesan con precisión y zona horaria según su campo. Los datos sensibles no se incluyen en QR. La configuración canónica evita que una cabecera externa determine el destino de un enlace.

## Ejecución y resultados

Seguir deploy/README.md para preparar secretos, construir, migrar y abrir http://localhost:8005/api/docs/. El mismo archivo explica cuentas, pruebas, parada y respaldo. No existen credenciales públicas predeterminadas. La base de prueba utiliza un servidor/rol separado para que el proceso de test no conceda CREATEDB al usuario operativo.

Resultados locales: 333 pruebas Django/API/contrato, 21 pruebas de políticas y 16 de importación; 30 respuestas HTTP comprobadas. Al recrear servicios sin borrar el volumen se conservaron dos activos ficticios. La aplicación ejecutó UID 10001 y rol PostgreSQL sin privilegios administrativos. El chequeo de modelos no detectó migraciones nuevas.

Los cuatro fallos de integración detectados se corrigieron y registraron en validacion.md y la bitácora. La demostración HTTP cubre el flujo principal y controles representativos; las suites cubren además otros módulos y reglas específicas. No se atribuye a esta ejecución una nueva comprobación visual del frontend ni del sitio Swagger dependiente de CDN.

## Seguridad y límites del producto

Se conserva sesión absoluta de treinta minutos, cinco fallos por cuenta/IP en quince minutos, CSRF y no-store. La autorización depende del rol y del objeto; no se deduce que autenticarse otorga acceso a todo recurso. Los cambios de datos y eventos mantienen autoría y antecedentes.

El despliegue HTTP se publica solo en loopback. check --deploy mantiene advertencias de HSTS, redirección y cookies Secure; no se declara producción pública segura. Los secretos son archivos locales protegidos/excluidos, no un servicio cifrado de gestión de claves. La navegación final del QR usa el frontend configurado, que se ejecuta aparte. Los importes físicos cero/negativos y la fecha documental de donación tienen rechazo explícito en el contrato actual; no se inventa soporte para esos casos.

La escalabilidad se apoya en separar procesos y conservar estado en PostgreSQL, pero no se certifica carga ni alta disponibilidad. La versión/digest fijados facilitan repetir el entorno; requieren mantenimiento cuando se actualizan dependencias o imágenes.

## Fuentes y anexos

- matriz-trazabilidad.md/json: los 104 vínculos y cinco RNF.
- catalogo-api.md/json: rutas inspeccionadas y contratos fuente.
- estandares.md y reflexiones-estandares.md: análisis y seis perspectivas del documento compartido.
- validacion.md y evidencia-validacion.json: resultados observados y sus límites.
- bitacora-integracion.md, ADR-0501 y despliegue.puml/png: decisiones, ajustes y despliegue.
- docs/semana-3/ y docs/semana-4/: arquitectura, contratos, amenazas y controles previos.
