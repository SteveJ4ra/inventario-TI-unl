# 009 - Consolidación técnica del backend de Unidad 1

Base: develop b60f52f. Alcance: contrato y evidencias de 002-008, sin nuevas funciones de negocio.

## Clarificaciones confirmadas (06/11/2026)

- Preparar Quarto para Pages y publicar después de revisar.
- Completar v1/OpenAPI del backend conservando rutas actuales.
- Mantener Compose local y evidencia reproducible con datos ficticios.

## Historias y aceptación

| ID | Historia | Criterios verificables |
|---|---|---|
| US-901 | Como gestor, quiero un contrato versionado común. | Todas las rutas/métodos tienen equivalente v1, permisos/servicios compartidos y compatibilidad /api/. |
| US-902 | Como consumidor, quiero conocer entradas/salidas/errores. | OpenAPI completo; cinco campos JSON; SVG/CSV separados; CSRF/revisión comprobados. |
| US-903 | Como responsable técnico, quiero comprobar el servicio sin exponer datos. | X-Request-ID; logs sin cuerpo/query; readiness SQL y 503 genérico. |
| US-904 | Como evaluador, quiero reproducir y entender el incremento. | Quarto, BPMN con DI, C4/UML, pruebas y restauración documentados/verificados. |

## Requisitos

| ID | Requisito | Verificación |
|---|---|---|
| FR-901 | Exponer rutas de negocio en v1 preservando /api/. | CompleteV1Tests y VersionedFlowTests |
| FR-902 | Documentar campos, permisos y archivos. | Cobertura rutas/métodos y exportación reproducible |
| FR-903 | Conservar envoltura y semántica HTTP. | Éxito/error, CSV/SVG, HEAD y métodos no admitidos |
| FR-904 | Registrar telemetría y readiness sin datos sensibles. | ObservabilityTests y healthcheck |
| FR-905 | Integrar Quarto, BPMN, C4/UML, ADR y trazabilidad. | Checks, XSD, DSL y revisión visual |
| FR-906 | Reproducir pruebas y restauración aisladas. | pytest/PostgreSQL y backup_roundtrip |

No se publica ni abre PR desde la preparación. Se conserva el estado PROPOSAL de la constitución, sin atribuir ratificación humana. Secretos, datos y dumps quedan fuera de Git.
