# Investigación y decisiones técnicas

**Fecha:** 2026-10-20. **Base funcional:** [spec.md](spec.md), DEC-001–DEC-036. Las siguientes decisiones concretan el cómo; no añaden procesos de negocio.

## R1. Mantener el backend y preparar React con Vite

**Decisión:** conservar Python 3.13, Django 5.2.18, DRF 3.16.1 y PostgreSQL 17 existentes. Preparar SPA React + TypeScript con Vite; sin SSR ni framework adicional, pues el backend ya existe y el acceso es privado.

**Razón:** reutiliza el stack acordado. Node local 22.23.1 cumple el mínimo documentado de Vite. Las consultas oficiales npm devolvieron React/React DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.4, plugin React 6.1.2, Vitest 5.0.5, Testing Library React 16.3.3, user-event 14.6.8, jsdom 30.1.3 y tipos React/React DOM 19.3.0. Fijar dependencias directas y conservar package-lock al instalar; los peers y el build serán comprobados entonces. El rango Node de jsdom exige 22.22.2+ en la rama 22, cumplido localmente.

**Alternativas:** cambiar Django por otro backend contradice el acuerdo; añadir SSR duplica responsabilidades sin necesidad aprobada. Bibliotecas adicionales de estado y navegación se difieren hasta que exista necesidad.

**Fuentes:** [React: aplicación desde cero](https://react.dev/learn/build-a-react-app-from-scratch), [Vite: requisitos y plantilla react-ts](https://vite.dev/guide/), [registro oficial de React](https://registry.npmjs.org/react/latest), [Vite](https://registry.npmjs.org/vite/latest), [TypeScript](https://registry.npmjs.org/typescript/latest), [Vitest](https://registry.npmjs.org/vitest/latest), [jsdom](https://registry.npmjs.org/jsdom/latest).

## R2. Sesión, CSRF y autorización de gestores

**Decisión:** usar sesión Django y un permiso DRF que exija usuario activo en grupo Gestores en cada endpoint de inventario. El superusuario administrativo también debe pertenecer al grupo para operar en el inventario. Login/logout de sesión con CSRF explícito; no hay registro público de cuentas.

**Razón:** resuelve el acceso privado de los gestores sin introducir tokens persistentes en el navegador. En desarrollo, Vite envía `/api` por proxy a Django; se configura origen de confianza local concreto. El login requiere protección CSRF aun antes de estar autenticado. Las credenciales incorrectas reciben un mensaje genérico.

**Alternativas:** JWT no es necesario para esta web y añade gestión de tokens; cualquier usuario autenticado no equivale a un gestor autorizado. La futura app móvil no se diseña en este incremento.

**Fuentes:** [DRF SessionAuthentication](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication), [Django CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/).

## R3. Códigos y unicidad normalizada

**Decisión:** secuencia PostgreSQL persistente NO CYCLE para producir códigos TI; restricción unique del código y restricciones funcionales Lower(Trim(...)) para marca/modelo/serie y correo. Limpiar datos al ingresar, conservar caracteres internos y detectar duplicados tanto en validación como en BD.

**Razón:** la BD protege las carreras que una comprobación previa no evita. Los números asignados por secuencia no se reciclan por rollback; se aceptan huecos técnicos sin prometer continuidad. La regla funcional es crecimiento sin reinicio ni reutilización.

**Alternativas:** MAX+1 sin bloqueo genera colisiones; serie globalmente única contradice DEC-009; retirar guiones o espacios interiores contradice DEC-030.

**Fuentes:** [PostgreSQL CREATE SEQUENCE](https://www.postgresql.org/docs/17/sql-createsequence.html), [funciones de secuencia y rollback](https://www.postgresql.org/docs/17/functions-sequence.html), [Django UniqueConstraint](https://docs.djangoproject.com/en/5.2/ref/models/constraints/#uniqueconstraint), [Trim](https://docs.djangoproject.com/en/5.2/ref/models/database-functions/#trim).

## R4. Ficha y evento dentro de una transacción

**Decisión:** un servicio por operación, con transaction.atomic y select_for_update sobre el activo; no bloquear mediante un join nullable del custodio. Comparar expected_revision después del bloqueo. Insertar evento y actualizar ficha en la misma transacción, capturando IntegrityError fuera del bloque fallido.

**Razón:** protege simultaneidad y rollback. La revisión impide que un formulario antiguo de devolución se aplique a una nueva entrega ocurrida entretanto. No es una nueva autorización ni flujo de negocio: asegura que la operación corresponde a la ficha que el gestor vio.

**Alternativas:** guardar ficha e historial por separado puede dejarlos contradictorios; bloquear después de validar puede usar datos obsoletos; confiar solo en botones deshabilitados no protege la API.

**Fuentes:** [Django transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).

## R5. Historial y rectificación limitada

**Decisión:** eventos con snapshots estructurados antes/después, vínculo único al objetivo rectificado y orden por identificador de evento dentro de cada activo. Las rectificaciones cuentan como operaciones posteriores. No exponer edición/borrado ni registrar estos modelos como admin editable; añadir protección de UPDATE/DELETE sobre Movement en PostgreSQL. Autor y fecha se obtienen en servidor.

**Razón:** permite restaurar exactamente condición, asignación, custodio y ubicación, conservar originales y prohibir retroceder a movimientos antiguos después de anular el último. Evita vías administrativas accidentales que eludan el servicio.

**Alternativas:** modificar el original contradice DEC-022; buscar el último evento ignorando rectificaciones vuelve elegibles antecedentes prohibidos. Un motor de event sourcing completo añade complejidad innecesaria: la ficha actual sigue almacenada.

**Fuentes:** [Django permisos de ModelAdmin](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_change_permission), [PostgreSQL triggers](https://www.postgresql.org/docs/17/sql-createtrigger.html). La decisión de inmutabilidad se deriva de FR-016/FR-022; no se atribuye a la documentación técnica una política institucional de auditoría.

## R6. Pruebas reales sobre PostgreSQL

**Decisión:** TestCase/APITestCase para reglas y contratos; TransactionTestCase con conexiones separadas y coordinación para bloqueos/concurrencia. Frontend con Vitest/Testing Library y verificación de navegador. Aislar la BD de pruebas y usar datos ficticios.

**Razón:** SQLite no prueba los bloqueos de PostgreSQL y TestCase puede ocultar uso de select_for_update fuera de atomic. El rol local de aplicación no dispone de CREATEDB; initdb y pg_ctl de PostgreSQL 17 están disponibles para levantar un clúster privado de prueba. Las pruebas no deben conceder privilegios al rol de la aplicación ni pedir contraseñas administrativas del entorno existente.

**Alternativas:** simular todas las carreras no verifica la BD real; alterar el rol productivo para test es innecesario. No se introduce pytest cuando unittest/DRF cubren el caso.

**Fuentes:** [Django TransactionTestCase](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#transactiontestcase), [base de pruebas](https://docs.djangoproject.com/en/5.2/topics/testing/overview/#the-test-database), [PostgreSQL initdb](https://www.postgresql.org/docs/17/app-initdb.html), [pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html).

## Incertidumbres al cerrar la investigación

La instalación de dependencias, build, migraciones, clúster aislado y pruebas ya se ejecutaron; resultados en [validation.md](validation.md). Se corrigió el lanzador Windows para capturar salida en archivo, evitando handles heredados, y se usó proveedor ICU en el clúster temporal para comparación Unicode de tildes. La base local existente usa Spanish_Ecuador.1252; no fue recreada. Fuente de la decisión regional: [PostgreSQL locale support](https://www.postgresql.org/docs/17/locale.html).

Permanecen fuera de esta validación los objetivos de producción y las políticas institucionales diferidas; no se atribuye ratificación al grupo.
