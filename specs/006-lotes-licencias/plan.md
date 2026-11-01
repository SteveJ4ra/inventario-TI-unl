# Plan: lotes de licencias

**Rama propuesta:** feature/lotes-licencias
**Fecha:** 2026-11-01 | **Spec:** spec.md

## Resumen

Agregar modelos, servicios y API para cantidades agregadas de puestos. El módulo es independiente del Asset y no altera su historial/custodia. Reutiliza usuarios Gestores, PostgreSQL, React y los estilos del proyecto.

## Contexto técnico

- Python 3.13, Django 5.2, DRF 3.16, PostgreSQL 17.
- React 19, TypeScript 7, Vite 8.
- Decimal no necesario para cantidades; usar enteros positivos/no negativos.
- No introducir claves de licencia ni adjuntos.
- No asociar este modelo a invoice/acquisition de hardware.

## Modelo y reglas

SoftwareLicenseLot con product_name, vendor, license_model USER_SEAT/DEVICE_SEAT, purchased_quantity, in_use_quantity, starts_on obligatorio, ends_on nullable, created_by/created_at/revision. LicenseLotAudit guarda actor, tiempo y before/after.
remaining_quantity se calcula; no se persiste como fuente de verdad. Temporal status se calcula: starts_on futura → Por iniciar; ends_on anterior a hoy → Vencido; otro caso → Vigente. Si ends_on es nulo no vence.
Un lote vencido mantiene remaining_quantity como conteo, pero UI lo denomina remanentes y marca Vencido.
Si purchased_quantity baja de in_use_quantity, rechazar hasta que gestor ajuste uso primero.

## API, interfaz y secuencia

Crear/listar/detallar/editar lotes, búsqueda/filtros, conteo manual de in-use auditado. Mismo Gestor role para todos. Contratos concretos en contracts/.
Migración no requiere tocar modelos existentes. Pruebas del modelo, servicio, permisos, concurrencia optimista y formularios antes de integrar.

## Constitution Check

Cumple trazabilidad y límites; evita catálogo de asignaciones individuales y proveedores externos. Revisar contra constitución ratificada antes de implementar.

## Contratos compartidos

Aplicar [contratos transversales](../../docs/sdd/contratos-transversales.md): sesión/roles, revisión global del activo, historial compatible, transiciones de localización y atomicidad. Esta referencia es parte del plan y de la validación de integración.
