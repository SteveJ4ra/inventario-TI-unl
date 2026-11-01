# Plan: bajas y aprobación

**Rama propuesta:** feature/steven-005-bajas-aprobacion
**Fecha:** 2026-11-01 | **Spec:** spec.md

## Resumen

Añadir estados de baja y flujo de aprobación específico para activos No localizados. Reutilizar autenticación de sesión del proyecto y grupos/permisos de Django; incorporar el permiso limitado de revisor y el operador técnico de cuentas. Mantener evidencia histórica append-only y proyecciones de estado actual transaccionales.

## Contexto técnico

Stack de 002: Python 3.13, Django 5.2, DRF 3.16, PostgreSQL 17; React 19, TypeScript 7, Vite 8. Pruebas API con Django y UI con Vitest/Testing Library. Facultad procede de 003; LifecycleStatus de 004.

## Componentes

- AssetLifecycleStatus: LOCATED, UNLOCATED, RETIRED.
- DecommissionEvent para baja normal o aprobada.
- DecommissionRequest con motivo, requester, assignee y estado PENDING/REJECTED/APPROVED/CANCELLED.
- ApprovalDecision inmutable, con resultado y motivo de rechazo.
- Cuenta Reviewer con faculty_id, active y must_change_password; autorización de endpoint específica, no permiso Gestor.
- Operator existente desde 003 para administrar cuentas revisoras. No es cargo institucional nuevo.
- Comando local deactivate_gestor; alta create_gestor existente permanece.
- UI separa bandeja de revisión y administración de cuentas. La lista Faculty de 003 es común.

## Integridad

1. Baja normal requiere lifecycle LOCATED, assignment AVAILABLE, custodian NULL y mantenimiento sin evento activo.
2. Baja de UNLOCATED requiere una solicitud aprobada por reviewer distinto y de faculty distinto.
3. Única solicitud PENDING por activo; recuperación cambia solicitud pendiente a CANCELLED con motivo predefinido y relación a RecoveryEvent.
4. Rechazo exige motivo; una nueva solicitud crea un registro nuevo con historial completo.
5. Reasignar solicitud crea un evento de reasignación; el operador no cambia autores/decisiones.
6. No permitir borrar; rectificar una baja errónea requiere el mecanismo de rectificación existente y motivo.
7. Password temporal no se vuelve a devolver por API; se almacena usando el hasher existente y force-change bloquea toda acción hasta cambio.

## Secuencia

1. Pruebas de transiciones, roles, faculty y recuperación durante aprobación.
2. Modelo de solicitud, decisión, baja y grupos/permisos.
3. Servicios atómicos de baja, solicitud, decisión, re-revisión y reasignación.
4. Actualizar autenticación para reviewer limitado y must_change_password.
5. Añadir comando deactivate_gestor.
6. Crear pantallas operador, Gestor y reviewer; mostrar solo datos requeridos.
7. Validar permisos, concurrencia, cancelación y retención de historia.

## Constitution Check

Trazabilidad y separación de funciones son centrales. La regla de doble revisión aplica solo a baja por No localizado, como confirmó el propietario. No extenderla a bajas normales ni inventar aprobadores institucionales. Estado constitucional sigue pendiente de ratificación.
## Integración con cambios de facultad

El servicio de cambio de facultad definido por 003 debe verificar, bajo bloqueo transaccional del activo, que no haya una solicitud de baja PENDING. La comprobación se implementa junto con la máquina de estados de solicitud; no se cambia la elegibilidad de una solicitud ya abierta.

Solo el Operator puede reasignar solicitudes pendientes, incluidas aquellas necesarias para desactivar un revisor. La operación registra actor, fecha, revisor anterior y nuevo.

## Contratos compartidos

Aplicar [contratos transversales](../../docs/sdd/contratos-transversales.md): sesión/roles, revisión global del activo, historial compatible, transiciones de localización y atomicidad. Esta referencia es parte del plan y de la validación de integración.
