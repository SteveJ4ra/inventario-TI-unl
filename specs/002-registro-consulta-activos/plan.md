# Plan de implementación: registro, consulta y custodia de activos

**Rama Git:** `feature/registro-consulta-activos` | **Fecha:** 2026-10-20 | **Especificación:** [spec.md](spec.md)
**Identificador lógico de Spec Kit:** `002-registro-consulta-activos`.
**Estado:** diseño ejecutado y validado localmente; evidencia en [validation.md](validation.md).

## Summary

Implementar los 23 requisitos confirmados mediante una aplicación Django `inventory`, API DRF y una interfaz React + TypeScript. La ficha muestra la situación vigente; los movimientos conservan su autor y las situaciones anterior/posterior. Entrega, devolución, cambio de condición y rectificación se ejecutan como operaciones transaccionales. Las rectificaciones añaden antecedentes, nunca reescriben el original.

La planificación se basa en DEC-001–DEC-036. La FPGA no añade una categoría. No se incorporan edición general, eliminación, mantenimiento mediante órdenes, importaciones, reportes, portal de custodios, aplicación móvil ni gestión web de cuentas. Se mantiene la configuración inicial del backend y el trabajo previo de `001-inventario-ti`.

## Technical Context

**Language/Version:** Python 3.13 (local 3.13.14), TypeScript 7.0.2, Node.js local 22.23.1, npm 10.9.8.

**Primary Dependencies:** mantener Django 5.2.18, DRF 3.16.1 y psycopg 3.3.6 del repositorio. Frontend previsto: React/React DOM 19.3.1, Vite 8.3.4 y plugin React 6.1.2. Versiones consultadas en el registro oficial npm; instalación, lockfile y build se validarán al implementar.

**Storage:** PostgreSQL 17, esquema relacional, restricciones de unicidad y estado; secuencia persistente para el código TI. Fechas con zona horaria, almacenadas en UTC y presentadas en America/Guayaquil.

**Testing:** Django TestCase/DRF APITestCase para datos, permisos y contratos; TransactionTestCase con conexiones independientes para carreras; Vitest 5.0.5 + Testing Library + jsdom para interacciones web; validación de navegador del recorrido completo. Sin obligación de TDD ni meta artificial de cobertura.

**Target Platform:** desarrollo en Windows PowerShell; comandos Python/npm reproducibles también en Linux. Navegador de escritorio y vista adaptable. Esta entrega no incluye despliegue público ni validación productiva.

**Project Type:** aplicación web con API y frontend separados dentro del mismo repositorio.

**Performance Goals:** sin SLA o volumen institucional aprobado. La aceptación mide exactitud de resultados, integridad y acceso; no se inventan tiempos ni capacidad. Paginación de activos de 50 elementos como decisión técnica de presentación.

**Constraints:** mismos permisos para gestores sobre todo el inventario; custodios sin cuenta; historial sin borrado automático; secretos fuera de Git. El usuario PostgreSQL de la aplicación no tiene CREATEDB: las pruebas utilizarán un entorno aislado preparado para ello. No cambiar sus privilegios para ejecutar tests.

**Scale/Scope:** incremento académico de seis historias, 23 requisitos y seis categorías fijas. Se validará con datos ficticios; objetivos de producción y retención institucional quedan para una etapa posterior.

## Constitution Check

La constitución continúa como **propuesta pendiente de ratificación**. Este control contrasta el diseño con sus principios sin atribuir una aprobación grupal inexistente.

| Principio / control | Antes de investigar | Después de diseñar |
|---|---|---|
| I. Necesidad → requisito → aceptación | Cumple: spec y 36 decisiones trazables. | Cumple: contratos, modelo y quickstart enlazan FR/SC; tareas y pruebas se enlazarán después. |
| II. Integridad | Cumple: estados e identidad definidos. | Cumple: unicidad en BD, bloqueo de activo, transacción, revisión y eventos con snapshots. |
| III. Acceso y secretos | Cumple: solo gestores y autor real. | Cumple: sesión + CSRF + grupo Gestores en cada endpoint; sin secretos, cuentas públicas o datos reales de demostración. |
| IV. Calidad verificable | Cumple: criterios comprobables. | Cumple: pruebas de permisos, reglas, rollback, concurrencia e interfaz; responsabilidades separadas sin repositorios genéricos. |
| V. Simplicidad y colaboración | Cumple: alcance validado. | Cumple: Django existente, un módulo de dominio, React sin estado global adicional; cambios revisables en rama feature. |

No se detectaron contradicciones de diseño que requieran una excepción a estos principios. Siguen pendientes la ratificación grupal y la reproducción por otro integrante; no se marcan como realizadas. Se revisará el código mediante PR a develop antes de integrarlo, conforme a CONTRIBUTING.md.

## Project Structure

### Documentation (this feature)

```text
specs/002-registro-consulta-activos/
  spec.md
  checklists/requirements.md
  plan.md
  research.md
  data-model.md
  contracts/api.md
  contracts/web.md
  quickstart.md
  tasks.md                    # etapa posterior speckit-tasks; aún no generado
```

### Source Code (repository root)

```text
backend/
  config/settings.py          # ajustes locales, auth y API
  config/urls.py
  inventory/
    models.py                 # persistencia y restricciones
    services.py               # operaciones atómicas y reglas
    serializers.py            # validación de entradas/salidas
    permissions.py            # gestor activo autorizado
    views.py                  # HTTP y consultas
    urls.py
    migrations/
    management/commands/create_gestor.py
    tests/test_assets.py
    tests/test_custody.py
    tests/test_permissions.py
    tests/test_concurrency.py
frontend/
  package.json
  package-lock.json
  vite.config.ts
  src/api.ts
  src/types.ts
  src/App.tsx
  src/components/
  src/styles.css
  src/tests/
```

**Structure Decision:** conservar backend/config y añadir una sola app de dominio. Servicios con funciones de responsabilidad concreta; modelos Django encapsulan persistencia y restricciones. Los serializadores no duplican las reglas de transición. Componentes React separan formulario, listado, ficha y movimientos; fetch centraliza sesión, CSRF y errores. La pantalla puede alternar lista/ficha mediante estado local, sin añadir un router en este incremento.

## Diseño y secuencia técnica

1. Modelos y migraciones: Asset, Custodian, Movement; secuencia de códigos, unicidad funcional y controles de estado. No registrar modelos del inventario como formularios editables en Django admin.
2. Acceso: sesiones Django, login protegido con CSRF y permiso de gestor activo perteneciente al grupo Gestores. Preparar comando interactivo de creación de gestores; no guardar contraseñas en comandos de ejemplo.
3. Registro/consulta: serializadores estrictos, filtros combinados y código generado en servidor. Catálogos fijos de categoría/condición/asignación; marca/modelo/ubicación permanecen texto.
4. Custodia: servicio atómico con bloqueo del activo y `expected_revision`; cada operación aceptada cambia ficha e inserta evento. Rectificación conserva snapshots y vínculo único al original.
5. Interfaz: sesión, registro de activos/custodios, listado con búsqueda/filtros, ficha, acciones válidas e historial; mensajes de carga, error y lista vacía. El servidor siempre vuelve a validar.
6. Verificación: casos de quickstart, pruebas automatizadas de riesgo e integración web/API; documentar resultados reales en la etapa de implementación.

### Integridad y corrección

- Crear código con `nextval` de secuencia PostgreSQL persistente `NO CYCLE`, formateando `TI-` + número con mínimo seis dígitos. No usar MAX+1. Puede haber huecos por intentos fallidos; no se promete numeración sin huecos ni orden de confirmación de solicitudes concurrentes.
- Unicidad de marca/modelo/serie y correo mediante expresiones Lower/Trim en PostgreSQL; limpiar espacios exteriores de las entradas. No eliminar caracteres interiores ni hacer casefold diferente de la comparación de BD.
- Movimientos: `atomic` → bloquear fila Asset → comparar revisión → comprobar estado y último evento → actualizar ficha → insertar evento → confirmar. Cualquier error revierte ambos cambios.
- La revisión aumenta en cada movimiento o rectificación. Una solicitud obsoleta devuelve conflicto y obliga a recargar; nunca se reintenta una escritura automáticamente desde la web.
- La elegibilidad de rectificación toma el último evento cronológico **incluidas rectificaciones**. Si el último es rectificación, no hay objetivo elegible hasta una operación nueva. El cliente no decide quién es autor ni qué snapshot restaurar.
- Historial inmutable por API y administración: sin PUT/PATCH/DELETE ni alta manual de eventos; protección de actualización/borrado en modelo y migración de trigger PostgreSQL para los originales. No se promete resistencia frente al dueño de la BD capaz de cambiar el esquema.

### Estrategia de validación

Cobertura funcional: historias 1–6 y SC-001–SC-016. Pruebas de API para cada FR; pruebas transaccionales de doble alta, código concurrente, doble entrega/devolución/rectificación y formulario obsoleto. Incluir rollback al fallar la inserción del evento. Pruebas web de filtros, errores y operaciones; recorrido manual en navegador con dos gestores y datos ficticios.

La BD de pruebas debe ser PostgreSQL, pues SQLite no reproduce estos bloqueos ni restricciones. En este equipo se dispone de initdb/pg_ctl de PostgreSQL 17 para un clúster temporal en work/ o un directorio privado de pruebas; se iniciará solo en loopback y se detendrá al terminar. El usuario de desarrollo existente no recibe CREATEDB. La implementación deberá aportar una forma reproducible de ejecutar esta validación sin publicar credenciales.

## Complexity Tracking

Sin excepciones a los principios evaluados. La secuencia, las transacciones y los snapshots responden a identidad, concurrencia y rectificación ya aprobadas. No se añaden microservicios, colas, autenticación JWT, event sourcing completo ni catálogos administrables.

## Artefactos y estado de la etapa

Investigación: [research.md](research.md). Dominio: [data-model.md](data-model.md). Contratos: [API](contracts/api.md) e [interfaz](contracts/web.md). Ejecución prevista: [quickstart.md](quickstart.md).

Las fases de diseño se completaron antes de tasks/analyze/implement. La implementación posterior quedó validada con pruebas, build y navegador; las dos migraciones del inventario están aplicadas en la base local. Véanse tasks.md y validation.md. La revisión humana y la integración mediante PR siguen pendientes.
