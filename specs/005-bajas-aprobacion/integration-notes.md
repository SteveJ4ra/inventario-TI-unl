# Activación e integración 005

Base de implementación: develop 161187c. No se han fusionado ramas de compañeros ni publicado PR nuevo.

1. Integrar primero proveedores reales 003/004: Faculty, permisos/sesión Operador, Asset.faculty y lifecycle_status, assignment nullable fuera de localizado, MaintenanceEvent.status y RecoveryEvent.asset. El adaptador usa Incident.type lost/stolen y last_custodian_snapshot para contexto. Confirmar los nombres reales y traducir en el adaptador si difieren; no duplicar modelos productivos.
2. Registrar retirement_models en inventory.models y generar migración contra el grafo real. Solo existe ahora 0003_retirement_movement_type: si otras ramas tienen otra 0003, resolver hojas con una migración merge sin alterar migraciones aplicadas. NO generar una migración productiva desde contract_tests.settings: incluiría proveedores falsos de tests.
3. Después de crear tablas 005, invocar install_retirement_guards desde una migración; FK reales y eventos auditados deben conservarse.
4. Combinar retirement_api y sus rutas con login/me/logout de 003 y urls.py, sin duplicar rutas ni permisos. La configuración contract_tests.urls enseña las rutas probadas, pero no debe usarse con datos reales.
5. Conectar assert_faculty_change_allowed dentro de la transacción y bloqueo del cambio de facultad en 003. Conectar cancel_for_recovery dentro de la transacción exterior de recuperación 004, validando recovery_event_id y revisión resultante antes de guardar el estado final.
6. ReviewerProfile: user_id, faculty_id y must_change_password no nulo; relación reviewer_profile. Grupos técnicos usados: Gestores, Operadores, Revisores. Confirmar constante Operadores con 003. Cuenta temporal no puede eludir cambio de contraseña por otros grupos.
7. Ejecutar todas las suites sobre los proveedores reales y revisar carreras/orden de locks con esas implementaciones. Las pruebas contract_tests usan syncdb y agregan campos mínimos solo a su registro de apps. Nunca activar esa configuración con una base de desarrollo real ni en producción.

El backend 005 ya contiene modelo/adaptador/HTTP y rectificación, pero no está disponible en la aplicación normal antes de estos pasos. La auditoría final debe revisar también nombres de tipos, permisos de grupos existentes, último custodio del reporte y migraciones.

La auditoría añadió context_snapshot en DecommissionRequest y FK RetirementAudit.recovery_event. La API no consulta custodios de incidentes posteriores. RecoveryEvent debe exponer incident_id y asset_id; cancelación verifica ambos contra solicitud/reporte. El puerto recovery_event_belongs_to_asset ahora recibe también request_id. Conservar la guarda temporal en IsManager al combinar permisos con 003, para que cuentas con múltiples grupos no eludan cambio inicial de contraseña.
