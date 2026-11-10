# Quickstart: CSV

1. Iniciar servicios según instrucciones de 002 y autenticar como Gestor.
2. Descargar plantilla de activos y completar filas de prueba con los requisitos de 003; probar también compra compartida y donación compartida.
3. Cargar un archivo válido, revisar vista previa y completar dos confirmaciones; comprobar códigos TI generados y activos Disponibles/sin custodio.
4. Repetir con una fila inválida/duplicada; verificar que todo el lote se rechaza sin crear activos.
5. Repetir con plantilla de lotes de licencias, incluyendo inicio obligatorio y cantidades inválidas.
6. Simular doble clic/reintento de confirmación y vencimiento de preview; verificar idempotencia y ausencia de parciales.

La implementación y las pruebas automáticas ya existen (ver `validation.md`). El recorrido manual de aceptación sigue pendiente porque la migración `0003` no se aplicó y los adaptadores de 003/006 aún no están integrados.

Antes de ejecutar Spec Kit, seleccionar `specs/008-importacion-csv` siguiendo [el índice SDD](../../docs/sdd/README.md#seleccionar-el-paquete-correcto-en-spec-kit) y verificar FEATURE_DIR. El chequeo solo verifica documentos; no ejecuta implementación ni pruebas de aceptación.
