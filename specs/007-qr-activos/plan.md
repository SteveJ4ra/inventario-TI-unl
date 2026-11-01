# Plan: QR de activos

## Contexto

La ficha autenticada y el código TI pertenecen a 002. Esta funcionalidad agrega una representación escaneable y un punto de entrada profundo, no una nueva autorización.

## Decisiones técnicas
- Mantener Django/DRF y React/Vite de 002.
- Generar SVG en el servidor con Segno; evaluar y fijar versión compatible en dependencias al implementar.
- Configurar `PUBLIC_APP_URL` por entorno; nunca formar enlaces a partir del encabezado Host de una petición no confiable.
- Ruta web pública de entrada solo muestra/login; endpoint API para SVG protegido por sesión Gestor.
- El cliente debe conservar el código solicitado tras login mediante estado/ruta permitida y volver a validar autorización.
- No guardar el SVG: es reproducible a partir de URL y código TI.

## Seguridad y errores

El QR y el código TI son identificadores, no secretos. Aplicar CSRF donde corresponda, autorización del endpoint de ficha, validación de redirección local, respuestas uniformes para códigos inexistentes y protección normal de sesión. No incluir información de custodio en URL.

## Despliegue

Configurar URL canónica HTTPS de la aplicación. Una modificación posterior puede hacer que QRs impresos apunten a una dirección antigua; documentar procedimiento de despliegue antes de imprimir a escala.

## Contratos compartidos

Aplicar [contratos transversales](../../docs/sdd/contratos-transversales.md): sesión/roles, revisión global del activo, historial compatible, transiciones de localización y atomicidad. Esta referencia es parte del plan y de la validación de integración.

La ruta web /assets/code/{code} resuelve por GET /api/assets/by-code/{code}/ autenticado. Mantener el contrato Asset existente; no usar búsqueda parcial del listado para resolver identidad.
