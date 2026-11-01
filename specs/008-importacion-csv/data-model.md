# Modelo de datos: importación CSV

Entidades de dominio resultantes: activos/adquisiciones de 003 y lotes de licencia de 006. No se conserva necesariamente el archivo original.

Entidad técnica `ImportBatch` propuesta:

| Campo | Regla |
|---|---|
| id | UUID opaco, no secreto de autorización |
| type | `ASSETS` o `LICENSE_LOTS` |
| schema_version | Versión de plantilla validada |
| state | `INVALID`, `PREVIEW_READY`, `CONFIRMED_ONCE`, `APPLIED`, `EXPIRED`, `CANCELLED` |
| content_hash | Vincula ambas confirmaciones al contenido validado |
| preview_summary/errors | Datos saneados para presentar y corregir |
| actor/timestamps | Gestor creador, fechas de carga, confirmación y aplicación |
| applied_result | Conteos/identificadores resultantes; idempotencia |

La persistencia de `ImportBatch` y el plazo de expiración se decidirán técnicamente con datos sensibles mínimos. La tabla no es fuente de verdad del activo/lote creado.
