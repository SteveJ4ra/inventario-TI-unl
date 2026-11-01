# Especificación: QR de activos físicos

**Rama propuesta:** feature/qr-activos
**Identificador:** 007-qr-activos
**Estado:** especificación preparada; no implementada.
**Decisiones:** DBE-033, DBE-045.

## Descripción

Generar un QR imprimible por activo físico que contiene un enlace interno identificable por código TI. El enlace no incluye datos personales. Al escanearlo fuera de la sesión, la aplicación solicita autenticación y, tras un acceso válido, abre la ficha correspondiente. Solo Gestores autenticados pueden consultar la ficha.

## Historias y aceptación

### US1 — Abrir una ficha desde QR (P1)
Como gestor, quiero escanear el QR de un activo para abrir su ficha, incluso si todavía no inicié sesión.

1. El QR contiene un enlace de la aplicación y el código TI; nunca incluye custodio, correo u otros datos de ficha.
2. Una solicitud sin sesión redirige al inicio de sesión conservando el destino solicitado de forma segura.
3. Tras autenticar, se resuelve el código y se muestra la ficha con los permisos existentes.
4. Código inexistente devuelve una respuesta de no encontrado, sin filtrar información.
5. El QR no concede autorización por sí mismo. Una cuenta no Gestor no accede a la ficha.

### US2 — Descargar e imprimir el QR (P1)
Como gestor, quiero descargar el QR en formato vectorial para imprimirlo y colocarlo en el activo.

1. Cada activo físico puede obtener su QR descargable, incluidos los que estén No localizados o dados de baja; la autorización sigue siendo obligatoria.
2. El QR puede regenerarse porque deriva de la URL y código estable del activo.
3. Cambiar `PUBLIC_APP_URL` cambia los enlaces generados; despliegues deben considerar los QR ya impresos.
4. No se generan QR para lotes de licencias.

## Requisitos funcionales

- FR-001: generar enlace interno con código TI y sin datos personales.
- FR-002: descargar QR SVG imprimible para un activo físico.
- FR-003: preservar destino interno tras login y rechazar redirecciones externas arbitrarias.
- FR-004: requerir autenticación y permiso Gestor antes de mostrar la ficha.
- FR-005: responder sin revelar datos cuando el código no existe.
- FR-006: construir URL desde `PUBLIC_APP_URL` configurada, no desde Host no confiable.
- FR-007: regenerar QR bajo demanda sin persistir imagen; no crear QR para licencias.
- FR-008: mantener acceso protegido en cualquier estado del activo.

## Criterios de éxito

- SC-001: un QR válido contiene enlace y código TI, sin custodio ni otros datos personales.
- SC-002: escanear sin sesión conduce a login y, tras autenticar como Gestor, abre la ficha identificada.
- SC-003: sesión sin rol Gestor no puede leer ficha ni descargar QR.
- SC-004: código inexistente y destino externo no exponen ficha ni crean redirección abierta.
- SC-005: la descarga SVG se puede escanear desde impresión de prueba y no requiere guardar imagen en base de datos.

## Límites

Sin acceso público a fichas, datos personales en QR, QR de licencias, seguimiento de escaneos, imágenes almacenadas ni rotación del código TI.
