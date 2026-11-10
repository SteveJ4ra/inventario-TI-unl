# Research: QR

| Tema | Decisión | Motivo |
|---|---|---|
| Contenido | URL HTTPS canónica con código TI | Permite escanear fuera de la app, iniciar sesión y continuar a la ficha sin exponer PII. |
| Formato de descarga | SVG | Vectorial para impresión y no requiere almacenar una imagen por activo. |
| Generador | Segno como opción técnica | Biblioteca Python enfocada en QR, con salida SVG. Fijar versión y verificar licencia/compatibilidad al implementar. |
| Autenticación | Reutilizar sesión de Gestor de 002 | QR no es mecanismo de autorización. |

Referencias técnicas primarias: [Segno en PyPI](https://pypi.org/project/segno/) y [documentación oficial de Segno](https://segno.readthedocs.io/). Estas referencias respaldan la alternativa técnica, no una decisión institucional.
