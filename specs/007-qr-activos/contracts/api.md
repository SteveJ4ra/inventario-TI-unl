# Contrato API: QR

Base bajo `/api/`; sesión y CSRF de 002.

## Descargar QR
`GET /api/assets/{asset_id}/qr.svg`

- `200 image/svg+xml`: QR vectorial como descarga o contenido SVG.
- `401`: sesión ausente.
- `403`: cuenta sin permiso Gestor.
- `404`: activo no encontrado.
- El QR codifica URL canónica derivada de `PUBLIC_APP_URL` y código TI.

La apertura del QR es una ruta web del cliente, no una API pública de ficha. Tras login, la ficha vuelve a consultar API autenticada. El destino de retorno nunca acepta URL absoluta arbitraria.
