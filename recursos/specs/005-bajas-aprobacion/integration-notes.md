# Activación e integración 005

Notas históricas de la implementación inicial. Base: develop 161187c. No se han fusionado ramas de compañeros ni publicado PR nuevo.

1. Integrar primero proveedores reales 003/004: Faculty, permisos/sesión Operador, Asset.faculty y lifecycle_status, assignment nullable fuera de localizado, MaintenanceEvent.status y RecoveryEvent.asset. El adaptador usa Incident.type lost/stolen y last_custodian_snapshot para contexto. Confirmar los nombres reales y traducir en el adaptador si difieren; no duplicar modelos productivos.
2. Registrar retirement_models en inventory.models y generar migración contra el grafo real. Solo existe ahora 0003_retirement_movement_type: si otras ramas tienen otra 0003, resolver hojas con una migración merge sin alterar migraciones aplicadas. NO generar una migración productiva desde contract_tests.settings: incluiría proveedores falsos de tests.
3. Después de crear tablas 005, invocar install_retirement_guards desde una migración; FK reales y eventos auditados deben conservarse.
4. Combinar retirement_api y sus rutas con login/me/logout de 003 y urls.py, sin duplicar rutas ni permisos. La configuración contract_tests.urls enseña las rutas probadas, pero no debe usarse con datos reales.
5. Conectar assert_faculty_change_allowed dentro de la transacción y bloqueo del cambio de facultad en 003. Conectar cancel_for_recovery dentro de la transacción exterior de recuperación 004, validando recovery_event_id y revisión resultante antes de guardar el estado final.
6. ReviewerProfile: user_id, faculty_id y must_change_password no nulo; relación reviewer_profile. Grupos técnicos usados: Gestores, Operadores, Revisores. Confirmar constante Operadores con 003. Cuenta temporal no puede eludir cambio de contraseña por otros grupos.
7. Ejecutar todas las suites sobre los proveedores reales y revisar carreras/orden de locks con esas implementaciones. Las pruebas contract_tests usan syncdb y agregan campos mínimos solo a su registro de apps. Nunca activar esa configuración con una base de desarrollo real ni en producción.

El backend 005 ya contiene modelo/adaptador/HTTP y rectificación, pero no está disponible en la aplicación normal antes de estos pasos. La auditoría final debe revisar también nombres de tipos, permisos de grupos existentes, último custodio del reporte y migraciones.

La auditoría añadió context_snapshot en DecommissionRequest y FK RetirementAudit.recovery_event. La API no consulta custodios de incidentes posteriores. RecoveryEvent debe exponer incident_id y asset_id; cancelación verifica ambos contra solicitud/reporte. El puerto recovery_event_belongs_to_asset ahora recibe también request_id. Conservar la guarda temporal en IsManager al combinar permisos con 003, para que cuentas con múltiples grupos no eludan cambio inicial de contraseña.

## Validación local con los proveedores de los PR

La rama local integracion/005-validacion parte de ba709bf (PR #19). La configuración normal de Django registra los modelos y rutas de 005. La migración 0007 une la rama de movimientos de baja con el esquema integrado y crea las protecciones de auditoría de PostgreSQL.

La recuperación guarda su evento y cancela la solicitud pendiente dentro de la misma transacción y bajo el bloqueo del activo. La cancelación y la recuperación consumen revisiones sucesivas. El cambio de facultad consulta solicitudes pendientes bajo el mismo bloqueo. La sesión usa las capacidades de 003 y añade retirement.review para revisores habilitados.

Las pruebas de inventario usan 003 y 004 reales. El entorno aislado queda en el historial. La suite de contrato usa ahora la configuración normal y los modelos reales, con un alias para el comando histórico.

### Resultado con Django y PostgreSQL reales

277 pruebas de inventario correctas, incluidas cuatro regresiones nuevas de integración 005. Se verificó aprobación y rectificación, cancelación al recuperar y bloqueo del cambio de facultad, rechazo de baja durante mantenimiento y conservación de la adquisición al dar de baja. También pasaron 21 pruebas aisladas de reglas y flujo.

## Revisión sobre develop a3d7128

Se incorporó el grafo de migraciones de los PR originales. La migración 0007 depende de 0006_integrate_features y 0003_retirement_movement_type. Las migraciones ya integradas en develop conservan su contenido. Para verificar este corte se usa el comando backend/tools/test_postgres.py inventory con la configuración normal del proyecto.
