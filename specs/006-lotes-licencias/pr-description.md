## Control de lotes de licencias

Agrega alta, consulta, búsqueda/filtros y edición auditada de lotes finitos por usuario o dispositivo. Un lote de 10 unidades con 4 en uso muestra 6 remanentes; si vence conserva el conteo y se etiqueta Vencido. Inicio obligatorio, fin opcional e inclusivo, cero permitido y uso limitado a compradas.

## Cambios

- SoftwareLicenseLot y LicenseLotAudit; migraciones 0004/0005 con constraints y trigger de historia inmutable.
- Cinco operaciones HTTP bajo `/api/license-lots/`: listado/alta, detalle/PATCH e historial. Sesión de Gestor, CSRF, entradas estrictas, paginación y revisión optimista con bloqueo transaccional.
- Pantalla Licencias integrada al inventario: formulario, filtros, remanentes, estados, edición e historial completo; 409 recarga sin reintentar.
- Proveedor público de 006 y delegación mínima del gateway 008 a su validador. Sin claves, facturas ni asignación individual; sin desarrollar flujos de otros paquetes.
- Runner PostgreSQL corregido para socket privado en Linux.

## Validación

72 pruebas backend en PostgreSQL 17 efímero, 16 pruebas puras de 008, 33 frontend y build correctos. Chrome real: dos gestores, alta/edición, vencimiento, historia, conflicto 409, CSRF, móvil y logout. Migraciones locales aplicadas conservando contenido legado.

npm audit sin avisos y Bandit sin hallazgos medios/altos. Se actualiza únicamente DRF de 3.16.1 a 3.18.2 para corregir cinco avisos conocidos, con autorización del responsable. La versión instalada y fijada se volvió a comprobar: 72 pruebas backend correctas, 33 frontend, 16 puras y navegador real; pip-audit no reporta vulnerabilidades conocidas. Las demás versiones y el lockfile frontend se conservan. No se declara certificación OWASP ni seguridad de producción; check --deploy conserva advertencias de HTTP local/DEBUG.

## SDD y revisión

[Especificación](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/spec.md), [tareas](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/tasks.md), [implementación](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/implementation.md), [validación](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/validation.md), [cinco revisiones](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/reviews.md), [integración](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/integration-notes.md), [API](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/contracts/api.md) y [web](https://github.com/SteveJ4ra/inventario-TI-unl/blob/feature/anderson-006-lotes-licencias/specs/006-lotes-licencias/contracts/web.md). T001–T013 implementadas; aceptación manual, revisión por otro integrante y ratificación grupal pendientes. La importación CSV de activos requiere 003; la de lotes se probó con 006 real.

Base de revisión: develop. No fusionar automáticamente.
