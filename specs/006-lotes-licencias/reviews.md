# Cinco revisiones de 006

2026-11-04, America/Guayaquil. Cinco pasadas realizadas por Codex sobre código, contratos, pruebas y ejecución real. Son revisiones asistidas por IA de la misma implementación; no se presentan como cinco revisores independientes ni como aprobación humana. Comandos/resultados en [validation.md](validation.md).

## Revisión 1 — Requisitos, contratos y alcance

Se contrastaron anderson.md, DBE-030/031/032/044, FR-001–012, SC-001–005, tasks, plan/modelo, contratos API/web y contratos transversales con los modelos, validadores, endpoints y pantallas finales.

| Punto revisado | Comprobación y conclusión |
|---|---|
| Unidad de registro | Cada SoftwareLicenseLot es un lote; no se crean asientos individuales ni vínculos a Asset/Custodian/adquisición. No se inventó unicidad de producto/proveedor. |
| Cantidades | Cero se admite; uso y compra enteros no negativos; uso <= compra se exige en servicio y DB. Rango integer documentado como decisión técnica. UI usa el mismo máximo. |
| Datos canónicos | vendor y revision se usan de extremo a extremo. expected_revision solo entrada PATCH. Estado/remanentes solo salida. No hay sinónimos incompatibles ni claves ocultas. |
| Vigencia | Inicio siempre obligatorio; fin opcional >= inicio. Día fin inclusivo. Estado y filtros derivan de timezone.localdate(), probado en UTC y Guayaquil cerca de medianoche. |
| Vencidos | No se borran ni se fuerza el remanente a cero; UI muestra Vencido y explica que el conteo no afirma disponibilidad utilizable. |
| Edición | Se auditan producto, proveedor, modalidad, ambas cantidades y ambas fechas; no solo uso. No se reemplazan eventos originales. |
| Permisos | Todos los Gestores activos tienen igual acceso; no se inventaron ámbitos por propietario para licencias. La propiedad del batch CSV sigue a cargo de 008. |
| Interoperabilidad | Se contrastó la firma real que busca 008: inventory.license_services.import_license_lots. Se entrega también validate_license_lot, sin implementar parser ni confirmaciones en 006. |
| Decisiones técnicas | Alta auditada en revisión 0; páginas de 50; JSON 16 KiB; edición sin cambios devuelve 400. Contratos ampliados con estas decisiones sin añadir funcionalidades. |

Hallazgo: 008 validaba solo presencia de modelo y podía anunciar preview válido con una cantidad fuera del rango de DB. Se agregó delegación mínima al validador de 006 y prueba real de rechazo antes de confirmar. No se reescribieron flujos de otro paquete.

Resultado: T001–T013 tienen código/evidencia trazable. La ratificación grupal sigue pendiente; la autorización del alumno para implementar no se registra como ratificación institucional.

## Revisión 2 — Seguridad de API y datos no confiables

Referencia: [OWASP API Security 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/). Se revisaron rutas expuestas, clases de permiso, autenticación de sesión, CSRF, métodos, entradas, salidas, errores, consultas y dependencias.

| Riesgo / superficie | Verificación realizada |
|---|---|
| API1/API5, autorización | GET lista/detalle/historial, POST y PATCH rechazan anónimo/inactivo/sin Gestores, incluso superusuario. Otro Gestor sí puede operar. Sin rutas para borrar o alterar auditoría. |
| API2, sesión | Cookie de sesión del cliente compartido; CSRF real para escrituras; origen ajeno rechazado; logout y 403 desmontan pantalla privada. No se introducen tokens o contraseñas en almacenamiento local. |
| API3, campos | Lista explícita de siete campos. Inyección de id/actor/tiempos/snapshots/revisión resultante/estado/remanentes/claves/asociaciones devuelve 400 sin escrituras. El servidor decide los metadatos. |
| API4, recursos | Lista e historial limitados a 50; texto de búsqueda 240, producto/proveedor 160. JSON tiene lectura real máxima de 16 KiB; no depende de Content-Length. Solo UTF-8, sin codecs de compresión. Se trata RecursionError de JSON como 400. |
| Inyección | Filtros con ORM parametrizado; texto de intento SQL devuelve lista vacía y conserva tablas. React muestra HTML malicioso como texto, sin crear un img. No hay eval, HTML dinámico ni URL remota consumida desde vendor/producto. |
| Errores y caché | Respuestas mantienen code/detail/fields; sin mensajes SQL en API. Endpoints 006 emiten no-store. JSON no objeto, formato roto, Unicode inválido y campos desconocidos no producen 500. |
| Cadena de dependencias | npm audit: 0 avisos. Bandit: 0 medios/altos en alcance indicado. pip-audit inicial: cinco avisos en DRF 3.16.1, conservados en evidencia. Anderson aprobó 3.18.2; versión fijada e instalada, suite repetida y auditoría final sin avisos conocidos. Solo DRF cambió. |
| Configuración | check --deploy muestra cinco advertencias reales de HTTP local/DEBUG. No se cambian cookies a Secure sobre HTTP local ni se simula un despliegue protegido por TLS. |

Hallazgos corregidos: JSON escalar heredado producía un ValueError al convertir errores; nombre de campo con surrogate producía UnicodeEncodeError al representar respuesta. Se incorporaron rechazos estructurados y regresiones. Ninguna prueba se silenció ni se cambió a skip.

Cierre del hallazgo: actualización puntual a DRF 3.18.2 autorizada por Anderson, aplicada a requirements y al entorno principal y comprobada de nuevo. Se utilizó la corrección del proveedor; no se dio por resuelta una vulnerabilidad global por endurecer solo el parser de 006. No se afirma que todas las pruebas de seguridad posibles estén cubiertas ni que exista certificación OWASP.

## Revisión 3 — Integridad PostgreSQL, transacciones y carreras

Se revisaron modelos, SQL generado de las dos migraciones, dependencias de migración, snapshots, uso de atomic/select_for_update y pruebas con conexiones concurrentes.

| Invariante | Evidencia |
|---|---|
| Uso y fechas válidos sin API | Inserciones ORM directas inválidas generan IntegrityError en PostgreSQL: negativos, exceso de uso, modalidad desconocida, inicio nulo y fin anterior. |
| Una revisión por modificación | Alta revisión 0; PATCH efectivo +1. UniqueConstraint de lote/resulting_revision evita eventos duplicados. Cambio obsoleto no altera ficha ni eventos. |
| Dos editores | Dos hilos/conexiones con barrera compiten sobre la misma fila: exactamente un éxito y un 409, revisión 1 y dos auditorías contando alta. Segundo escenario en navegador con dos Gestores reales. |
| Atomicidad de alta/edición | Se provoca un fallo en auditoría mediante mock de ese punto; DB real revierte alta o edición. El mock no reemplaza proveedor ni persistencia. |
| Atomicidad de importación | Gateway/servicios reales. Fallo de segunda fila revierte la primera, eventos y estado del batch; reintento posterior crea exactamente dos. Idempotencia de 008 conserva cantidad. |
| Inmutabilidad | Guardas save/delete más trigger PostgreSQL. Se probaron bulk update/delete y DELETE SQL; tampoco se puede duplicar evento para una revisión. FK PROTECT conserva referencias. |
| Historia reconstruible | Antes/después incluyen los siete campos y revisión. actor_label conserva el nombre original cuando la cuenta se renombra; actor/timestamp provienen del servidor. |
| Migraciones y legado | Grafo 0001→0002→0003→0004→0005, sin alteraciones funcionales de las antiguas. SQL de 0004/0005 revisado antes de migrar local. Hashes de filas previas coinciden; tablas nuevas vacías. |
| Aislamiento del runner | Socket en directorio temporal privado, credenciales efímeras y puerto loopback libre. El rol de la aplicación no recibe CREATEDB; sus bases y .env no se usan en las suites. |

Hallazgo corregido: el runner original intentaba crear socket/lock en /var/run/postgresql y no exponía el log PostgreSQL que explicaba el error. Corrección mínima específica POSIX; Windows conserva su ruta previa. Se ejecutó la suite completa tras la corrección.

Resultado: constraints, rollback, migraciones y carreras comprobados en PostgreSQL 17.11 real. No se extrapola este resultado a modelos de 003/004/005 ausentes.

## Revisión 4 — Interfaz, sesión y experiencia de uso

Se revisaron App, cliente API, formularios, listado, detalle, historia, estados de carga/error y estilos. Se ejecutaron 13 pruebas nuevas de interacción y el recorrido real de Chrome con una DB aislada.

| Flujo | Comprobación |
|---|---|
| Navegación | Licencias se integra en la barra existente, sin reemplazar Inventario/CSV. Se evita cargar consultas de activos al estar en Licencias. En móvil la navegación permanece visible. |
| Formulario | Obligatorios, límites de cantidades/fechas, fin vacío → null, valores cero y preview de remanentes. Errores del servidor se muestran con nombres de campo comprensibles, sin borrar lo escrito. |
| Envíos | Botón y fieldset deshabilitados mientras guarda; doble clic produce una solicitud. PATCH incorpora método, CSRF, cookies y expected_revision; se preservan POST existentes. |
| Concurrencia | 409 cierra el formulario anterior, recarga detalle/historial y pide revisión; prueba verifica que no hay segundo PATCH automático. En navegador se confirma conteo y auditoría tras dos gestores. |
| Consulta | Búsqueda y filtros combinables, limpieza y paginación. Estado de red fallida se distingue de una lista vacía; existe consulta manual de nuevo. AbortController cancela lecturas al desmontar/cambiar. |
| Historial | Alta/ediciones ordenadas, autor registrado, hora local de visualización, revisión y antes/después de todos los campos. Páginas independientes de la lista de lotes. |
| Vigencia | Etiquetas Por iniciar/Vigente/Vencido vienen del backend. Texto aclara uso de remanentes vencidos. No se deduce disponibilidad desde el contador ni desde el reloj del navegador. |
| Privacidad y XSS | Strings se renderizan con React; sin HTML inyectado. 403/logout vuelven a login y desmontan los datos. Prueba de HTML no crea nodos ejecutables. |
| Vista estrecha | Chrome 375×812, navegación visible, sin desborde horizontal. Captura completa con datos ficticios inspeccionada por Codex; no se versiona como dato del alumno. |
| Regresión | 20 pruebas previas siguen pasando; total 33 y compilación TypeScript/Vite correctos. |

Hallazgo: selector de modalidad sin nombre explícito no fue localizable por la coincidencia exacta del primer recorrido automatizado. Se agregó aria-label, se repitió la prueba y pasó. La evidencia de navegador es automatizada; aceptación manual por Anderson sigue pendiente.

## Revisión 5 — Reproducción, Git, documentación y límites

Se revisaron el diff completo desde el commit base, archivos compartidos, requisitos/lockfile, selectores SDD, evidencias y comandos de entrega.

| Revisión | Resultado / criterio |
|---|---|
| Rama y base | Rama exclusiva feature/anderson-006-lotes-licencias sobre develop 4247cc8998ed810fdb6462941d85f3324260a2ec, verificada con fetch antes de implementar. No se fusionaron ramas de compañeros. |
| Cambios compartidos | Models/services/serializers/views/urls y App/api/types/styles ampliados para 006. Único ajuste de 008: su gateway consume el validador público; justificado por prueba de integración real. No hay implementación de otros paquetes. |
| Herramientas | Único cambio de versión: DRF 3.16.1 → 3.18.2, aprobado por seguridad. Comparación del entorno confirmó que solo cambió ese paquete; package-lock sin cambios. Black/Prettier, auditores y Playwright se usaron desde entornos de herramientas sin agregarlos al stack de la app. |
| Secretos y artefactos | .env, venv y node_modules ignorados; sin credenciales, DB, capturas privadas ni logs temporales en commits. Se verifica también contenido del diff contra valores privados en memoria, sin imprimirlos. |
| SDD | Selector explícito con NO_PERSIST=1; no se reinicializa Spec Kit ni se regenera Constitución. Tareas se marcan solo al contar con código y evidencia. Se documentan participación de IA y revisión humana pendiente. |
| Evidencia | Conteos reales: 72 backend/33 frontend/16 puras; se distinguen DB real, red simulada, fallo inyectado y navegador. Fallos previos y correcciones conservados. No se reutilizan conteos históricos de 002 como evidencia nueva. |
| Entorno local | Nuevas migraciones aplicadas tras revisión; registros anteriores conservados. No se recreó gestor ni se cambiaron contraseñas o .env. Pruebas de navegador no ensucian la DB local. |
| Entrega | Siete commits descriptivos revisados; publicación de la rama y PR hacia develop autorizados después de la implementación. La URL se obtiene de GitHub al crear el PR; sin merge automático. |
| Pendientes humanos | Aceptación manual, revisión por integrante y ratificación grupal. Decisión de DRF resuelta por el alumno y actualización comprobada. La integración global con 003 sigue fuera del alcance de 006. |

Criterio de cierre: funcionalidad local implementada y verificable; publicación de rama y PR autorizada expresamente por el alumno tras el cierre local. Auditoría de dependencias repetida sin avisos conocidos tras aplicar DRF 3.18.2. Aprobación humana, producción e integración global siguen pendientes de forma explícita. Ninguna de estas cinco revisiones equivale a aprobar el proyecto para producción.
