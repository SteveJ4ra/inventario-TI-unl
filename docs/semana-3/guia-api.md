# Consultar la API y los activos actualizados

Con el backend preparado según `backend/README.md` y ejecutándose en `127.0.0.1:8000`, abrir `http://127.0.0.1:8000/api/docs/`. El esquema JSON del subconjunto se encuentra en `http://127.0.0.1:8000/api/openapi.json`.

La página incluye Swagger UI y una tabla de activos. Para ver datos se necesita una sesión de gestor autorizada. Se puede iniciar sesión en la aplicación web usando el mismo host `127.0.0.1`, o utilizar en Swagger `GET /auth/csrf/` y después `POST /auth/login/` con el valor devuelto en el encabezado `X-CSRFToken`. La cookie de sesión se conserva en el navegador. No existen credenciales predeterminadas.

La tabla consulta `/api/v1/assets/` cada cinco segundos mientras la página está visible. Así muestra cambios confirmados por otros gestores en la siguiente consulta exitosa, sin recargar el navegador. Permite cambiar de página y consultar manualmente. Se consulta la página seleccionada; no se descargan todos los activos a la vez. Los permisos se comprueban en cada petición y la tabla se limpia si se pierde el acceso. Si la conexión falla, la página lo informa; los datos solo vuelven a actualizarse cuando una consulta tiene éxito. Este mecanismo utiliza consultas periódicas, no WebSockets.

La página Swagger obtiene sus archivos de un CDN fijado a la versión 5.17.14 y requiere conexión para mostrarlos; la tabla y el esquema JSON se sirven desde el backend. La API histórica `/api/` sigue atendiendo a la aplicación existente. La versión `/api/v1/` cubre el recorrido documentado, no todos los módulos.
