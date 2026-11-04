# Notas de integración de 004

El 4 de noviembre de 2026, la rama de trabajo, `develop` y la referencia local `origin/develop` coincidían en `4247cc8998ed810fdb6462941d85f3324260a2ec`. El trabajo de 004 está en el árbol de trabajo. La referencia remota local debe actualizarse antes de publicar.

| Dependencia | Estado |
|---|---|
| 002 | Presente. 004 reutiliza activos, custodios, Gestores, CSRF, operaciones y movimientos. El historial legado y la rectificación se verificaron en regresión. |
| 003 | Fuera del alcance de 004. La integración posterior debe revisar modelos, migraciones, sesión y revisión global compartida. |
| 005 | Pendiente. `recover_asset` indica dónde cancelar una solicitud pendiente bajo el mismo bloqueo y transacción. 005 debe aportar ese servicio y probar la carrera entre recuperación y aprobación, el orden de bloqueos y el rollback completo. |
| 008 | Presente en la base. Las regresiones de CSV usan el gateway de prueba existente. |

`0004` depende de `0003_importbatch` y `0005` de `0004`. Ambas se probaron en PostgreSQL real temporal y constan aplicadas en la base de desarrollo con autorización previa. Al integrar ramas, comprobar colisiones de migraciones del mismo app y dependencias entre ellas. Preservar las migraciones ya aplicadas.

El `git fetch origin` previo a publicar confirmó que `origin/develop` seguía en `4247cc8`. Las ramas remotas de 006 y 007 tienen cambios paralelos aún fuera de esa base. 006 añade `0004_license_lots` y `0005_license_lot_audit_immutable` y comparte modelos, servicios y rutas con 004. Si ambas cadenas llegan a `develop`, habrá que conciliar sus dependencias de migración y repetir las regresiones. 007 comparte vistas, rutas y la ficha web. El equipo debe revisar esos puntos cuando integre los PR.

La ficha consume el historial unificado y las rutas de novedades y mantenimiento. Publicar frontend y backend compatibles con el esquema 0005. El historial ordena por revisión global descendente. La formulación anterior del contrato local se alineó con el contrato transversal sin cambiar criterios funcionales.

Se recomienda un PR **normal para 004** una vez autorizado, porque el alcance independiente funciona con 002 y el recorrido en navegador se verificó con los servicios reales. La integración de 005 se revisará en su propio alcance. Antes de integrar a `develop`, el equipo debe revisar el PR, ratificar el alcance y registrar la decisión sobre la Constitución propuesta. Si al actualizar `develop` aparece una colisión que impida repetir la validación, usar Draft hasta resolverla.

## Publicación pendiente de autorización

1. Ejecutar `git fetch origin develop` y comparar `git rev-parse origin/develop` con el commit base registrado. Si avanzó, revisar el diff y el grafo de migraciones antes de integrar cambios.
2. Preparar dos commits con selección explícita de los [archivos revisados](implementation.md#archivos-para-revisión). Usar `feat: implementar novedades y mantenimiento del paquete 004` para código, migraciones, pruebas y runner. Usar `docs: cerrar validación SDD del paquete 004` para README, contratos y evidencias.
3. Antes de cada commit, ejecutar `git diff --cached --check` y `git diff --cached --stat`. Mantener fuera los archivos ignorados de entorno, dependencias y build.
4. Tras aprobar los commits y la publicación, ejecutar `git push -u origin feature/yandri-004-novedades-mantenimiento`.
5. Crear el PR con `gh pr create --base develop --head feature/yandri-004-novedades-mantenimiento --title "feat: 004-novedades-mantenimiento" --body-file specs/004-novedades-mantenimiento/pr-description.md` y solicitar revisión de otro integrante.
