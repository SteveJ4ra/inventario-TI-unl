# Incremento de semana 3: API versionada del recorrido de activos

## Necesidad y alcance

Un gestor necesita registrar, consultar, entregar y recibir un activo con evidencia verificable. El incremento presenta ese recorrido y el acceso por sesión bajo `/api/v1/`; conserva `/api/` para clientes existentes. La facultad y el documento de adquisición deben existir y se preparan mediante la API existente. No amplía a v1 las operaciones de importación, bajas, licencias u otros módulos.

## Criterios de aceptación

1. Una solicitud JSON admitida en v1 responde con `success`, `message`, `data`, `errors` y `meta`, salvo respuestas que no admiten cuerpo y HEAD. Las respuestas de error contienen datos de error sin exponer detalles internos de errores HTML.
2. El alta válida genera código, queda disponible y conserva facultad y adquisición. Los errores de entrada o identidad no crean un alta parcial.
3. Un gestor consulta la ficha, entrega el activo operativo a un custodio y registra la devolución con condición y ubicación. Se conservan los controles y el historial existentes.
4. Sesión, autorización, CSRF, validaciones y revisión concurrente se aplican también a v1. La API previa mantiene sus rutas y formato.
5. El contrato OpenAPI identifica su alcance; `/api/openapi.json` y `/api/docs/` ofrecen el esquema y Swagger UI. La página Swagger carga sus archivos desde un CDN y requiere conexión para mostrarse.
6. La página de documentación consulta la página de activos seleccionada cada cinco segundos mientras está visible, para mostrar cambios de otros gestores sin recargar. Solo muestra datos con sesión de gestor; permite paginar y actualizar manualmente. Al perder autorización limpia la tabla.

## Componentes y verificaciones

Las rutas se declaran en `backend/inventory/urls_v1.py`. El adaptador `api_v1.py` encapsula respuestas; las vistas y servicios anteriores mantienen las reglas de negocio y transacciones. La prueba `inventory.tests.test_api_v1` verifica el recorrido, errores, CSRF, permisos y compatibilidad de la API previa. Las demás pruebas del proyecto cubren las reglas específicas de los módulos.

El esquema presenta el flujo principal; no se afirma que documente la totalidad del backend. La condición de presentación al docente y las observaciones recibidas deben registrarse cuando sucedan.

Las entregas y devoluciones conservan subrutas de operación tipadas (`deliver/` y `return/`) para delegar en las transacciones probadas del sistema. Se consideró crear movimientos con `POST /movements/` y un tipo en el cuerpo; esa alternativa unificaría la colección de eventos, pero obligaría a introducir otro despacho y migrar contratos. No se permite modificar custodia o condición mediante un PATCH genérico en la ficha v1.
