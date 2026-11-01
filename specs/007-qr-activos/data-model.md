# Modelo de datos: QR

No se requiere tabla nueva. Datos derivados:

| Dato | Origen |
|---|---|
| Código TI | Activo físico existente, estable y único. |
| URL QR | `PUBLIC_APP_URL` + ruta interna de resolución + código TI. |
| SVG | Generación bajo demanda; no persistido. |

La ruta de retorno al completar autenticación se valida contra rutas internas permitidas. El QR no contiene id de custodio, nombre, correo, estado ni token de acceso.
