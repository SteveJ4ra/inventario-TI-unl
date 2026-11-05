# Contrato HTTP de la API del incremento 002

**Estado:** contrato implementado y comprobado localmente; evidencia en [validation.md](../validation.md). Base local prevista `/api/`. JSON UTF-8. Las entradas de escritura son objetos JSON; el login también rechaza listas y valores escalares con HTTP 400. Identificadores internos enteros positivos; etiquetas de interfaz en español.

## Acceso y errores comunes

Sesión Django con cookie HttpOnly; peticiones de escritura incluyen cookie CSRF y cabecera `X-CSRFToken`. El login exige CSRF también como anónimo. Todos los endpoints de datos, opciones e historial requieren usuario activo del grupo Gestores, incluidos superusuarios administrativos que operen en inventario. No hay registro público de cuentas ni acceso del custodio.

Formato de error de la API: `{"code":"invalid","detail":"Revisa los datos indicados.","fields":{"name":["Este campo es obligatorio."]}}`. fields es opcional. El middleware CSRF también debe devolver JSON legible para estas rutas, con code csrf_failed. No exponer excepciones SQL ni credenciales.

| HTTP | Significado |
|---|---|
| 200 | Consulta, login o logout completado. |
| 201 | Activo, custodio o movimiento creado. |
| 400 | Campos vacíos, formato/enum inválido, campos desconocidos o reservados aportados por cliente; credenciales incorrectas con mensaje genérico. |
| 403 | Sin sesión/autorización o CSRF inválido; distinguir code de acceso y CSRF para la interfaz. |
| 404 | Recurso inexistente. |
| 405 | Método que no está expuesto. |
| 409 | Duplicado de identidad, revisión obsoleta, estado incompatible o rectificación inelegible. |

No permitir que el cliente sustituya código, autor, timestamps, snapshots, revisión resultante ni custodia inicial. Se rechazan campos reservados/extra en escrituras; respuestas readonly no implican aceptar esos campos en entrada.

## Sesión

| Método / ruta | Entrada | Salida |
|---|---|---|
| GET `/auth/csrf/` | Ninguna; puede ser anónimo. | 200, `{"csrfToken":"..."}` y cookie CSRF. |
| POST `/auth/login/` | username y password obligatorios; CSRF. | 200 con gestor `{id,username}` autorizado; sesión establecida. Credenciales inválidas 400, usuario sin autorización 403 sin sesión de inventario. |
| GET `/auth/me/` | Sesión. | 200 `{id,username}` del gestor; sin permiso 403. |
| POST `/auth/logout/` | Sesión y CSRF. | 200 `{"detail":"Sesión cerrada."}`; invalida sesión. |

Tras login el cliente obtiene un token CSRF actualizado antes de nuevas escrituras, pues Django puede rotarlo. No guardar
a contraseña ni tokens en localStorage.

## Activos

GET `/assets/`: listado paginado de 50, orden id descendente; `page` entero positivo. Respuesta `{count,next,previous,results:[Asset]}`. Filtros:

| Parámetro | Regla |
|---|---|
| search | Fragmento sin distinguir mayúsculas: OR entre code, name, brand, model, serial_number y full_name/email del custodio actual. Vacío equivale a sin búsqueda. |
| category | Una categoría admitida. |
| condition | operativo, averiado o en_reparacion. |
| assignment | disponible o asignado. |
| location | Valor exacto de ubicación actual seleccionado entre los valores presentes; sin catálogo administrable. |
| custodian | ID de custodio actual. |

El parámetro adicional situation admite disponible, asignado, no_localizado y baja. Disponible selecciona activos localizados con asignación disponible y sin mantenimiento en curso; asignado selecciona localizados con asignación asignada. Los otros valores filtran el ciclo de vida. Un valor inválido devuelve 400. Los parámetros anteriores se conservan y se combinan con situation mediante AND.

Todos los filtros presentes se combinan con AND y se combinan con el resultado de search. Un valor enum, ID o page inválido devuelve 400; criterios válidos sin coincidencias devuelven lista vacía. No se busca el custodio anterior de activos Disponibles como si fuera el actual.

GET `/assets/{id}/`: Asset o 404.

POST `/assets/`: campos requeridos name, description, category, brand, model, serial_number, location y condition. assignment y current_custodian los establece el servidor como disponible/null; no se admiten en entrada. Respuesta 201 Asset. Validar longitudes según data-model.md y no aceptar textos obligatorios vacíos tras trim. Duplicado de combinación normalizada 409 (code duplicate_asset).

```json
{
  "name": "Portátil de laboratorio",
  "description": "Equipo para prácticas del grupo",
  "category": "portatil",
  "brand": "Ejemplo",
  "model": "A1",
  "serial_number": "LAB-001",
  "location": "Laboratorio 1",
  "condition": "operativo"
}
```

Asset de salida: id, code, todos los campos de alta, assignment, current_custodian (objeto Custodian o null), revision, created_at, created_by `{id,username}`, rectifiable_movement_id (entero o null). Este último es una ayuda de presentación; el servicio vuelve a validar dentro del bloqueo.

No exponer PUT/PATCH/DELETE del activo ni endpoints para modificar su identidad o código.

## Custodios y valores de selección

GET `/custodians/`: lista de Custodian ordenada por nombre e id, para seleccionar persona. POST misma ruta: full_name y email requeridos, department opcional. Respuesta 201 Custodian `{id,full_name,email,department}`. Validar formato de email sin whitelist, comparar unicidad sin mayúsculas/espacios exteriores; duplicado 409 (duplicate_custodian). No crea User ni cuenta.

GET `/options/`: listas `{categories:[{value,label}],conditions:[{value,label}],assignments:[{value,label}],locations:[string]}`. Categorías seis fijas; locations son valores distintos ya registrados en activos, para filtrar. Esta ruta no administra catálogos ni limita la captura textual de nuevas ubicaciones.

## Movimientos

Todas las rutas siguientes requieren gestor, CSRF y `expected_revision` entero no negativo igual a revision vigente. Una revisión distinta devuelve 409 stale_revision y no escribe. El cliente vuelve a consultar y deja que el gestor repita conscientemente la acción; no reenvía automáticamente.

| POST / ruta relativa | Datos requeridos además de expected_revision | Datos opcionales |
|---|---|---|
| `/assets/{id}/deliver/` | custodian_id, destination | note |
| `/assets/{id}/return/` | condition, reception_location | note |
| `/assets/{id}/condition/` | condition distinta, reason | note |
| `/assets/{id}/rectify/` | movement_id, reason | note |

Respuesta 201 `{"asset":Asset,"movement":Movement}`. Las reglas y efectos son los de la tabla de transiciones de [data-model.md](../data-model.md). Datos requeridos vacíos → 400; activo inexistente → 404; custodio de entrega inexistente → 400 con campo; estado incompatible → 409 invalid_state. Objetivo de rectificación ajeno, inexistente o inelegible → 409 ineligible_rectification sin modificar ninguno de los activos.

Ejemplo de entrega: `{"custodian_id":1,"destination":"Aula 2","expected_revision":0,"note":"Para práctica"}`. El autor y el instante de registro siempre son del servidor.

GET `/assets/{id}/movements/`: lista cronológica descendente por id de Movement del activo; sin edición/borrado. Campos: id, asset_id, type, occurred_at, actor `{id,username,recorded_label}`, custodian (persona registrada históricamente o null), before/after `{condition,assignment,custodian_id,location}`, note, reason, rectifies_id (o null), rectified_by_id (o null), resulting_revision. Conservar original y mostrar la rectificación por su vínculo; obtener rectified_by_id sin modificar el original.

Se conservan todos los eventos sin borrado automático. Nunca se habilita una segunda rectificación del mismo movimiento ni rectificar una rectificación. Movimiento anterior con sucesores sigue siendo inelegible aunque el último haya sido anulado. Dos solicitudes simultáneas se validan sobre el estado bloqueado y vigente.

## Relación con requisitos y verificación

Activos/options: FR-001–FR-009, FR-015, FR-021. Sesión/autor: FR-010–FR-011, FR-014. Custodios: FR-019. Rutas de movimiento: FR-012–FR-018, FR-020, FR-022–FR-023. Los tests de API comprobarán estado HTTP, cuerpo, ausencia de escritura en rechazo y coherencia ficha/eventos; no basta verificar solo un 200/201.
