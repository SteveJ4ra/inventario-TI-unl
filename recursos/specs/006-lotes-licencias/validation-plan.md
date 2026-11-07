# Plan de validación: 006

**Estado:** implementación local y casos funcionales ejecutados; resultados, fallos corregidos y límites en [validation.md](validation.md). Auditoría de dependencias repetida tras actualizar DRF 3.18.2, sin avisos conocidos; revisión humana pendiente.

- Cálculo entero compradas − en uso y límites negativos/superiores.
- Inicio obligatorio; fin opcional; estados temporales derivados.
- Fecha de fin vencida conserva remanentes y muestra Vencido.
- Auditoría antes/después de actualización de uso.
- Aislamiento frente a activos, custodios, facturas y claves.
- Permisos, concurrencia/revision, filtros y formulario web.

## Casos de integración de revisión final

Cantidad cero se acepta conforme a FR-003; negativas se rechazan. Fin anterior a inicio se rechaza; mismo día de fin es vigente, siguiente es vencido. PATCH obsoleto devuelve 409.
