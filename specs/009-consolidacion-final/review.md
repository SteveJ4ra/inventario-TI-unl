# Análisis de consistencia 009

Se contrastaron las respuestas de alcance con las reglas 002-008, el registro de rutas, serializadores, servicios y pruebas. No se introducen asignaciones de licencias, traslados ni roles institucionales adicionales.

## Hallazgos corregidos

1. Cobertura parcial de v1: se comparten las rutas de negocio completas y se prueba igualdad de rutas/métodos.
2. Tipos ReadOnly mal inferidos e historial restringido: se consultan metadatos de relaciones y se conservan diccionarios JSON extensibles; las respuestas reales validan con JSON Schema.
3. Orden XML de incoming/outgoing: se corrigió según XSD BPMN oficial.
4. Alias C2 implícito: se enlaza la API declarada y se regenera la figura.
5. Caché pytest no escribible: se deshabilita en el contenedor efímero; suite final sin advertencia.

Se preservan las rutas antiguas, los permisos por objeto, la auditoría y las migraciones existentes. La constitución mantiene PROPOSAL. Publicación y PR requieren revisión posterior. No hay conflictos funcionales conocidos en el ensayo local; los límites de entorno/documentación se registran explícitamente.

6. Secretos con modo 600 no legibles por UID de contenedor en Linux: ACL de lectura acotada por UID, probada sin cambiar propietario ni permitir lectura a otros usuarios; CI prepara este permiso explícitamente.
