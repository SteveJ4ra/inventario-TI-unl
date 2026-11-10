# Perspectivas individuales del dossier compartido

Las seis perspectivas desarrollan un argumento técnico y lo relacionan con una evidencia concreta. La publicación de archivos se identifica por separado en el historial Git; el análisis compartido no atribuye commits nuevos a quien no los haya publicado.

## Alex - Información, contratos y migraciones

Mi conclusión es que compartir el mismo framework no garantiza que dos módulos interpreten igual un dato. Una factura compartida necesita total documental e importe individual; confundirlos alteraría los valores del inventario. HTTP y JSON facilitan transmitirlos, mientras el contrato y las restricciones definen qué significan. La prueba de factura compartida y la plantilla de migración incluida en el contenedor muestran que reproducibilidad también requiere conservar los artefactos usados para validar datos históricos. No sustituiría una facultad desconocida por una inventada para lograr que una migración pase. Evidencia: test_several_assets_reuse_invoice_and_keep_exact_individual_values y test_legacy_preflight.py.

## Yandri - Estado, mantenimiento y trazabilidad

En el ciclo de vida distingo condición, asignación y situación de localización. Un equipo operativo en mantenimiento no está disponible para entregar solo porque funcione; una pérdida tampoco demuestra una devolución. El API necesita expresar esas reglas y dejar antecedentes, además de responder con JSON. Los snapshots y la transacción permiten mantener una explicación coherente aun si una reparación se interrumpe por robo. Relaciono mantenibilidad con conservar esa separación en servicios y pruebas, no con añadir estados para cada pantalla. Evidencia: test_preventive_maintenance_blocks_delivery_and_closes_without_changing_condition y test_loss_during_maintenance_and_recovery_preserve_original_evidence.

## Steven - Autorización y evidencia de la operación

Considero que autenticación y autorización deben evaluarse por separado. Una sesión válida no habilita a un gestor para aprobar una baja de No localizado; interviene el revisor asignado y la independencia de facultad. Un token sin expiración o una aprobación sin antecedente no resuelven ese riesgo. Los contratos de bajas y las pruebas de carreras entre recuperación y aprobación muestran por qué el servidor conserva la decisión y el evento original. El despliegue debe mantener esas reglas aunque cambie el servidor HTTP. Evidencia: contract_tests/test_api.py y test_recovery_and_approval_cannot_both_commit.

## Anderson - Reproducibilidad y límites de los contenedores

Mi análisis de portabilidad parte de un límite: usar Docker no prueba que la aplicación funcione en cualquier equipo. El error de finales de línea y el locale de PostgreSQL muestran diferencias concretas entre anfitrión y contenedor. Por eso valoro fijar versiones, separar pruebas y verificar una recreación completa. En licencias, el remanente numérico no se vuelve cero por caducar la vigencia; el contrato debe distinguir ambas ideas para que otro cliente no interprete mal los puestos. Evidencia: ADR-0501, persistencia y test_zero_remaining_and_temporal_boundaries.

## Pedro - QR, transporte y configuración confiable

El QR es una forma de transportar un identificador hacia una ruta, no un permiso de lectura. Su destino debe salir de configuración y no de una cabecera Host elegida por el cliente. La demostración local permite HTTP solo en loopback con permiso explícito, mientras mantiene el rechazo de destinos externos inseguros con DEBUG=false. Esa distinción permite probar el backend sin presentar localhost como un servicio institucional con TLS. Evidencia: test_host_alternativo_no_define_destino_qr y QrLocalDeploymentTests.

## Emilio - Importación e integridad entre módulos

Mi conclusión es que una respuesta de éxito debe representar el resultado completo prometido. En una importación, validar cada fila por separado no basta si luego se guardan algunas y otras fallan. La vista previa inmutable, las dos confirmaciones y la transacción hacen comprobable el compromiso de todo o nada. El estándar de intercambio y el proveedor de dominio cumplen funciones distintas: CSV organiza el archivo; adquisiciones y licencias mantienen sus reglas al aplicar el lote. Evidencia: test_ciclo_doble_confirmacion_y_reintento_idempotente y test_fallo_del_proveedor_revierte_y_permite_reintentar.
