# Observación y ajuste de la página de la API

## Observación recibida

El docente solicitó una presentación visual de la API accesible mediante un enlace local, en lugar de mostrar solamente JSON. También se aclaró que los cambios realizados por otros usuarios debían aparecer sin recargar la página.

## Análisis y decisión

La solicitud corresponde a la página para explorar la API; no exige crear una nueva aplicación de inventario. Se mantuvo Swagger UI para consultar y probar las operaciones y se añadió un panel de activos que consulta al servidor cada cinco segundos mientras está visible. El panel permite paginar y actualizar manualmente.

## Ajuste y comprobación

La página está disponible en `/api/docs/` y consume `/api/v1/assets/` mediante la sesión de gestor. Cada consulta verifica los permisos; si se pierde el acceso se limpia la tabla. Una prueba en Chrome con dos sesiones y PostgreSQL temporal comprobó que el activo creado por un gestor aparece al otro sin recargar. Los cambios se reflejan en la siguiente consulta exitosa; no hay una conexión de eventos instantánea.

El esquema OpenAPI también se ofrece en `/api/openapi.json`. Swagger UI requiere cargar sus recursos desde un CDN fijado a una versión; la tabla y el esquema se sirven desde el backend.
