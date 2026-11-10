# Plan y tareas de semana 3

## Decisiones de diseño

El adaptador de rutas y respuestas se limita a v1 y delega a las vistas y servicios existentes. Esto permite presentar el contrato común sin cambiar las respuestas que consume la interfaz actual. Los datos de la colección se conservan íntegros en `data`, incluida su paginación. Los errores existentes se conservan dentro de `errors`; `meta` comienza como objeto vacío.

OpenAPI describe el subconjunto versionado, no todo `/api/`. La documentación y las pruebas deben evolucionar con los módulos restantes. La página Swagger UI utiliza recursos externos fijados a una versión: el esquema JSON sigue disponible localmente si el CDN no carga.

La observación docente solicitó una página visual para la API y actualización de cambios de otros usuarios. `/api/docs/` conserva Swagger UI y consulta la página de activos seleccionada cada cinco segundos, usando los permisos existentes. No requiere recargar el navegador; los cambios se observan en la siguiente consulta exitosa.

## Lista de verificación

- [x] Seleccionar registro, consulta, entrega y devolución como recorrido principal.
- [x] Elaborar análisis textual y modelos C1–C3 y UML del código pertinente.
- [x] Proponer seis ADR vinculados a necesidades y alternativas.
- [x] Implementar rutas v1, formato común y conservación del contrato anterior.
- [x] Documentar el subconjunto mediante OpenAPI y una página Swagger.
- [x] Validar estructuralmente el contrato OpenAPI y comprobar los recorridos y errores implementados.
- [x] Ejecutar la suite de backend, las pruebas del frontend y una demostración HTTP con sesión y CSRF.
- [x] Validar los diagramas PlantUML, el modelo DSL y las fuentes técnicas utilizadas. Los ADR quedan propuestos para revisión del equipo.
- [x] Preparar borradores de informes AA, ACD y APE y guías de publicación.
- [ ] Registrar los PR reales, las aportaciones y la retroalimentación docente cuando existan.
