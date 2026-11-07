# Operación y demostración del backend

## Cuentas individuales

Con web iniciado, ejecutar en una terminal interactiva:

```powershell
docker compose -p inventario-ti-u1-final exec web python manage.py create_gestor
docker compose -p inventario-ti-u1-final exec web python manage.py create_operator
```

Los comandos solicitan usuario y contraseña sin publicarla; aplican validadores. Cada persona usa su cuenta; no existe una credencial universal de demostración. El operador administra facultades/revisores por /api/v1/operator/. Al crear revisor se define facultad y contraseña temporal; debe cambiarla por /auth/change-password/ antes de decidir. El gestor se desactiva con `deactivate_gestor`; consultar --help para su argumento y confirmación. No usar superusuario para demostrar permisos del inventario.

## Recorrido reproducible de extremo a extremo

1. Mostrar el problema, spec 002 y BPMN/C4 en Quarto.
2. Mostrar /health/ready/, OpenAPI y Swagger; obtener CSRF, iniciar sesión y renovar CSRF.
3. Como operador, crear facultad si no existe; como gestor, registrar documento PURCHASE con reference, document_date, supplier, invoice_total e items vacío.
4. Crear custodio con nombre/correo; crear activo con facultad/documento, datos descriptivos, valor individual y fecha o motivo de desconocimiento.
5. Consultar su código TI y revisión. Intentar devolver sin custodia: 409, sin cambio.
6. Entregar a la persona con destino y revisión; consultar Asignado, custodio e historial.
7. Devolver con revisión, condición y recepción; verificar Disponible/sin custodio y dos antecedentes.
8. Mostrar QR SVG (enlace sin datos personales; requiere frontend configurado para navegación final).
9. Mostrar pruebas automatizadas, logs y X-Request-ID; explicar 30 min absoluto y 429 sin esperar media hora en clase. El smoke fuerza caducidad únicamente de su sesión ficticia.
10. Mostrar un mantenimiento que bloquea entrega y un lote de licencias vencido con remanentes; para bajas/CSV usar contratos y pruebas integradas, sin sustituir el flujo real por mocks.

El ejemplo HTTP de alta usa IDs obtenidos realmente, no valores supuestamente existentes. Las cuentas/activos ficticios del smoke quedan identificados como tales y sus cuentas se desactivan al finalizar.

## Instalación y límites

Seguir portal/operacion.qmd y deploy/README.md. Puerto del ensayo final: 8007; el predeterminado de Compose sigue siendo 8005. La aplicación React no está incluida en Compose. Swagger necesita acceso al CDN de swagger-ui; el esquema, live.js, backend y portal se conservan localmente. Para un dispositivo externo, configurar URL/HTTPS alcanzable y orígenes explícitos; loopback no es una publicación institucional.

## Evidencia y conservación

No subir .env, deploy/.secrets, dumps, archivos con cookies/CSRF ni datos de personas reales. Los resultados públicos de validación deben ser agregados y sanitizados. El backup de ensayo se restaura solamente en su base temporal; no sustituye la política de respaldo de la universidad. Los plazos institucionales de historial/respaldos se definen fuera de este incremento académico.
