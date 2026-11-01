# Plan de validación: QR

**Estado: pendiente; sin pruebas ejecutadas.**

- Pruebas unitarias de contenido SVG/URL y ausencia de PII.
- Pruebas de integración de sesión, permiso Gestor, not-found y configuración canónica.
- Pruebas frontend del retorno al destino después del login.
- Revisión manual con escaneo de SVG impreso y rutas válidas/no válidas.
- Evidencia requerida: resultados de tests, capturas de flujo y versión/configuración probada.

## Casos de integración de revisión final

Código TI se resuelve exactamente tras login sin conocer id numérico; cuenta sin sesión/permiso recibe 403 conforme a 002. No hay redirección externa.
