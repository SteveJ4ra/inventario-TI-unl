# feat: 004-novedades-mantenimiento

Base `develop` · rama `feature/yandri-004-novedades-mantenimiento`.

## Alcance

- Novedades de daño u observación con alertas y resolución auditada.
- Mantenimiento preventivo y correctivo con bloqueo de entrega, ubicación previa y recepción confirmada.
- Pérdida o robo con último estado conocido e interrupción de taller, y recuperación con inspección y código conservado.
- Historial por revisión global y evidencia inmutable. Se conserva el contrato legado de movimientos.
- T001–T017 y FR-001–FR-016 del alcance independiente de 004.

## API y esquema

Rutas y cargas útiles en [contracts/api.md](contracts/api.md). Las migraciones `0004_asset_lifecycle_events` y `0005_asset_transition_evidence` amplían el modelo de custodia y añaden evidencia protegida por PostgreSQL. Ambas están aplicadas en la base de desarrollo. El plan de migraciones quedó vacío.

## Verificación

83 pruebas de backend en PostgreSQL temporal con ICU, 26 de frontend y build TypeScript/Vite aprobados. `manage.py check`, comprobación de migraciones y `git diff --check` pasaron. Chrome real verificó el flujo completo de 004 con Vite, Django y PostgreSQL temporal, diez revisiones y dos movimientos legados reales. Las pruebas de componentes sí usan API simulada.

## Evidencia y revisión

- [Especificación](spec.md), [plan](plan.md) y [tareas](tasks.md).
- [Implementación](implementation.md), [validación](validation.md) y [notas de integración](integration-notes.md).
- [Quickstart](quickstart.md) con reproducción automatizada y manual.

La integración con 005 requiere el servicio real de cancelación y pruebas conjuntas de concurrencia. La Constitución sigue como propuesta. Se solicita revisión de otro integrante antes de integrar. Se recomienda PR normal para 004 si la validación se mantiene al actualizar la base. Se usó Codex como asistencia de implementación y validación.

En la comprobación previa a publicar, `origin/develop` seguía en `4247cc8`. Las ramas paralelas 006 y 007 comparten archivos con 004. Al integrar 006 habrá que revisar también las dos cadenas de migraciones de `inventory` que parten de `0003`. Ver [notas de integración](integration-notes.md).
