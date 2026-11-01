# Contrato API: QR

Base bajo `/api/`; sesión y CSRF de 002.

## Descargar QR
`GET /api/assets/{asset_id}/qr.svg`

- `200 image/svg+xml`: QR vectorial como descarga o contenido SVG.
- `403`: sesión ausente o permiso insuficiente.
- `403`: cuenta sin permiso Gestor.
- `404`: activo no encontrado.
- El QR codifica URL canónica derivada de `PUBLIC_APP_URL` y código TI.

La apertura del QR es una ruta web del cliente, no una API pública de ficha. Tras login, la ficha vuelve a consultar API autenticada. El destino de retorno nunca acepta URL absoluta arbitraria.

## Resolver el enlace escaneado

GET `/api/assets/by-code/{code}/` requiere Gestor y devuelve el mismo Asset de GET por id, o 404. Registrar esta ruta antes de la ruta numérica si el router lo requiere. El QR usa `PUBLIC_APP_URL` + `/assets/code/{code}`; la ruta web conserva destino tras login y consulta este endpoint. No buscar por coincidencia parcial ni requerir un id interno dentro del QR. Conservar códigos incluso para activos dados de baja.
