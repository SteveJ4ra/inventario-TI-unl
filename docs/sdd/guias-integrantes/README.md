# Guías individuales para agentes de código

Entregar a cada integrante su archivo completo junto con acceso al repo y SDD. Paquetes completos asignados en el orden de nombres recibido; no se dividieron funcionalidades. El número de tareas no equivale a esfuerzo.

| Integrante | Guía/paquete | Rama | Tareas |
|---|---|---|---|
| Alex | [003-fichas-adquisiciones](alex.md) | `feature/alex-003-fichas-adquisiciones` | T001–T018 |
| Yandri | [004-novedades-mantenimiento](yandri.md) | `feature/yandri-004-novedades-mantenimiento` | T001–T017 |
| Steven | [005-bajas-aprobacion](steven.md) | `feature/steven-005-bajas-aprobacion` | T001–T019 |
| Anderson | [006-lotes-licencias](anderson.md) | `feature/anderson-006-lotes-licencias` | T001–T013 |
| Pedro | [007-qr-activos](pedro.md) | `feature/pedro-007-qr-activos` | T001–T010 |
| Emilio | [008-importacion-csv](emilio.md) | `feature/emilio-008-importacion-csv` | T001–T014 |

Los seis pueden desarrollar y abrir PR en paralelo. 005 consume 003+004; 008 consume 003+006. El trabajo aislado y el PR no esperan sus merges; migración/validación integral sí necesitan proveedores reales. Las guías exigen declarar limitaciones y prohíben fakes en producción. La integración debe respetar dependencias y no dejar develop roto deliberadamente; después se hace la auditoría conjunta acordada.

Publicar la base documental antes de distribuir. Si no está en develop, las guías explican cómo incorporar solo esa rama documental a una feature nacida en develop; no incorporar implementaciones de compañeros.
