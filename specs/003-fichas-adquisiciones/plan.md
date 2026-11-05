# Plan: administración de fichas y adquisición

**Rama autorizada de trabajo:** Alex_Sigcho_Feature; destino develop
**Fecha:** 2026-11-01
**Spec:** spec.md

## Resumen

Extender los modelos existentes sin rehacer el registro 002. Se agregan facultades, documentos de adquisición compartidos y líneas por activo, auditoría de edición de ficha/custodio y controles para fecha de adquisición y moneda fija USD. Se mantiene Django/DRF/PostgreSQL y React/TypeScript.

## Contexto técnico

- Backend existente: Python 3.13, Django 5.2, Django REST Framework 3.16, PostgreSQL 17.
- Cliente web existente: React 19, TypeScript 7 y Vite 8.
- Pruebas: unittest/TransactionTestCase existentes y Vitest/Testing Library.
- Persistencia: migraciones Django y restricciones PostgreSQL donde aporten integridad.
- No agregar almacenamiento de archivos ni servicio institucional.
- Configuración: valor de moneda único, por ejemplo ASSET_CURRENCY_CODE=USD; no modificarlo desde la UI.

## Reglas de diseño

1. Faculty usa una identidad estable y nombre administrado por operador. Facultades referenciadas no se borran; la corrección conserva identidad.
2. AcquisitionDocument distingue PURCHASE y DONATION. Los campos requeridos dependen de ese tipo.
3. AcquisitionLine enlaza el documento con un activo y valor individual; el total de factura/documento no se duplica por línea.
4. AcquisitionDate se guarda en la línea del activo; fecha desconocida exige motivo. No usar una fecha centinela.
5. AssetChange y CustodianChange guardan snapshots previos/nuevos, usuario y timestamp de servidor. La edición de activo exige motivo. El cambio de facultad usa operación separada de Operator y auditoría propia; 005 agrega la protección por solicitud pendiente.
6. Las operaciones usan transacción atómica y bloquean el activo antes de validar campos únicos.
7. Un cambio de facultad/documento usado no altera el historial de adquisición; las correcciones quedan auditadas.
8. Migraciones preservan activos preexistentes sin inventar facultad, fuente o factura. Se debe preparar una etapa explícita de completado de legado antes de aplicar obligatoriedad a los registros históricos.

## Contratos y estructura

API propuesta en contracts/api.md; web en contracts/web.md. La organización de código reutiliza backend/inventory/models.py, services.py, serializers.py, views.py, urls.py y sus pruebas. La interfaz se añade en frontend/src/components y en el cliente existente.

## Secuencia técnica

1. Añadir modelos Faculty, AcquisitionDocument, AcquisitionLine y auditorías.
2. Completar manualmente el mapeo de facultad de todos los activos existentes con datos verificados antes de migrar; luego migrar y exigir facultad en cada ficha. Si falta información, detener esa migración hasta resolverla, sin asignar valores ficticios.
3. Implementar servicios transaccionales para documentos compartidos y ediciones auditadas.
4. Añadir serializadores con validación condicional por compra/donación y campos reservados rechazados.
5. Exponer endpoints y permisos de gestor/operador; la facultad solo cambia por ruta del operador.
6. Añadir pantallas de datos de adquisición, edición de activo/custodio y administración de facultades.
7. Validar invariantes, historial, concurrencia y escenarios con pruebas y guía.

## Constitution Check

- Trazabilidad: cumple mediante documentos y auditorías.
- Integridad: requiere restricciones para líneas/documentos/duplicados.
- Seguridad: la lista de facultades queda exclusiva del operador; gestores no pueden cambiar roles.
- Simplicidad: sin adjuntos, contabilidad ni integración externa.
- Estado de constitución: propuesta pendiente de ratificación; revisar contra su versión ratificada antes de implementar.

## Riesgos y resolución

- La lista real de facultades no está disponible: el operador la carga manualmente; no inventar valores institucionales.
- Datos existentes podrían no tener adquisición/facultad: migración no debe fabricar información. Completar con datos verificados mediante saneamiento autorizado; fixtures solo en entornos de prueba.
- Una factura contiene conceptos no asignables: no imponer que suma de líneas sea igual al total de factura, pues impuestos/envío podrían diferir.

## Contratos compartidos

Aplicar [contratos transversales](../../docs/sdd/contratos-transversales.md): sesión/roles, revisión global del activo, historial compatible, transiciones de localización y atomicidad. Esta referencia es parte del plan y de la validación de integración.

## Fundamentos de acceso y creación sin dependencia circular

Introducir aquí el comando local `create_operator`, permiso de Operador y adaptación de login/me/logout conforme al contrato transversal. 003 debe poder administrarse sin que 005 exista.

Primero se registra el documento compartido de adquisición (metadatos; sin exigir ids de activos aún inexistentes). `POST /api/assets/` se amplía con `faculty_id`, `acquisition_document_id`, `item_value` y fecha de adquisición o motivo de desconocimiento, junto con los campos de 002. Crea activo y AcquisitionLine en la misma transacción. Las líneas opcionales en el alta del documento solo enlazan activos ya existentes. Así el registro manual y CSV usan el mismo servicio sin crear activos incompletos intermedios.

Preparar el mapeo verificado de facultad antes de migrar; crear tabla/columnas, cargar facultades y aplicar el mapeo antes de exigir NOT NULL. La adquisición histórica no se inventa: agregar esquema compatible y no activar restricciones obligatorias sobre datos legados hasta completar los datos verificados; para nuevas altas exigirlos desde la activación del flujo 003. No sustituir datos reales por fixtures en una migración de despliegue.

Importes Decimal y código de moneda se guardan en el documento y en snapshots. La configuración central define moneda de nuevos registros; cambiarla en el futuro no reetiqueta importes históricos. No se incorpora conversión monetaria ni selector visual.

## Preparación T001–T003 — 2026-11-04

Alex confirmó fecha/motivo en AcquisitionLine, support_type + reference para donación y evento documental más un AssetChange por activo afectado en cada corrección compartida. No se supone equivalencia con support_description de CSV 008.

Los modelos se preparan sin migración: T004 incorporará Asset.faculty en fases y protección SQL de auditorías. Precisión monetaria técnica Decimal(12,2), compatible con MAX_MONEY de 008; no se agrega una regla funcional sobre suma, cero o negativos sin aclararla. Las validaciones clean no sustituyen serializadores ni servicios, y save no llama automáticamente full_clean.


## Corrección técnica autorizada tras auditoría — 2026-11-04

Preparar CHECK de textos no blancos (regex \S) para obligatorios de 002 y entidades nuevas, guardas ORM de conservación y evidencia solo insertable. Declarar revisión positiva y unicidad por activo/revisión en cada auditoría de activo/facultad. La exclusión entre tablas y coherencia con Asset.revision se garantizarán mediante servicios transaccionales T006, no mediante un CHECK que consulte otra tabla.

Diseño SQL pendiente, sin migraciones generadas: protección UPDATE/DELETE de evidencia y DELETE de dominio; revisar TRUNCATE/privilegios. Antes de instalar constraints de textos sobre legado, preflight y resolución humana de incompatibilidades; no sanear datos por suposición. Revisar integration-notes.md para el diseño y sus límites.

No se consideran aprobadas políticas de cero/negativos, adaptación de support_description, fecha de donación, cambio de origen con líneas ni protocolo completo de concurrencia de documentos. Las tres confirmaciones previas de Alex conservan su alcance; el modelo permisivo no añade aprobación. No activar NOT NULL de facultad antes de adaptar la escritura T005–T007.


## Primera expansión T004 autorizada — 2026-11-04

0004_acquisition_expansion depende de 0003_importbatch, añade siete entidades y Asset.faculty nullable sin default. No realiza backfill. Nueve CHECK ya definidos de textos sobre Asset/Custodian se instalan NOT VALID: no inspeccionan/reparan legado, pero sí rechazan nuevas escrituras inválidas. Una fase posterior requiere completado verificado y VALIDATE CONSTRAINT antes de afirmar saneamiento. Nuevas tablas usan constraints aprobados; sin política de signo monetario ni restricciones sobre fecha de donación/cambio de origen pendientes.

La migración instala triggers UPDATE/DELETE para evidencia nueva y DELETE para activos/documentos/líneas, mantiene Movement/ImportBatch y bloquea su reversión automática por Django. No protege operaciones administrativas TRUNCATE/DROP; revisión de privilegios pendiente. Pruebas en PostgreSQL temporal: 10 expansión y selección de regresión 75/75. No aplicada localmente; T004 continúa parcial.


## Inicio T005/T006 — implementación parcial 2026-11-04

Primitivas de adquisición se concentran en acquisition_services.py; services.create_asset conserva 002 durante la transición y deriva a alta completa 003 cuando recibe sus campos. La validación compartida vive en serializers.py. Código/secuencia de activo se reutilizan, y documento/facultad se comprueban bajo transacción antes de activo+línea. No hay adaptador CSV con reglas duplicadas.

Base de actualización auditada: snapshot previo/nuevo (incluyendo adquisición y currency persistida), expected_revision bajo lock, incremento y AssetChange en una transacción. Asociar un activo existente exige revisión/motivo y no reasigna una adquisición vigente. Orden documento→facultad (alta)→activo/línea; no se considera resuelto el protocolo pendiente para editar metadatos compartidos. La rectificación de servicios y la consulta assets exigen igualdad de revisión global.

Sin implementación de T007–T018: no se exponen endpoints ni UI. Cero/negativos y fecha documental explícita en donación devuelven pending_decision antes de escribir; no son políticas funcionales decididas por el agente. Edición documental/cambio de origen/import_assets siguen pendientes. Regresión seleccionada 92/92; aceptación API aún roja. T005/T006 permanecen parciales.


## Compras web T008–T010 — 2026-11-04

AcquisitionForm compone el formulario base de Registration en dos pasos: documento nuevo/cargado, después cada activo+línea. App conserva el componente y su bloqueo al ocultarlo y lo descarta al salir de la sesión. Tipos/cliente usan el transporte existente; importes string e ids numéricos, moneda de respuesta. La ficha readonly diferencia total compartido y valor individual. get_document en acquisition_services centraliza lectura y prefetch; no hay nueva lógica de creación ni un lote ficticio.

Errores preservan datos y factura; solo respuestas confirmadas añaden códigos/líneas. Éxitos previos se conservan cuando falla un activo posterior. No se fusiona por referencia, se copia fecha documental al activo ni se promete idempotencia tras una respuesta perdida. API de items iniciales existentes sigue pendiente, al igual que los asuntos de T001–T007; no se avanza a T011–T018. Evidencia: 124 backend, 34 frontend, build PASS, sin DB local.

## Cierre técnico vigente — 2026-11-04

PATCH documental confirmado por Alex: reason, expected_document completo y mapa expected_revisions por activo; lock documento → activos por id, comparación de metadatos/pertenencia/revisiones y evento documental + AssetChange por activo en una transacción. Documento sin activos usa snapshot y evento documental. No se cambia source ni moneda.

Proveedor import_assets 003/008 implementado en acquisition_imports.py y expuesto por acquisition_services.py. Reutiliza serializadores y altas reales, agrupa exclusivamente por document_key del lote, respeta documento existente y se integra en la transacción e idempotencia de ImportBatch. Donaciones nuevas por CSV permanecen explícitamente bloqueadas por Alex; las que referencian documento existente funcionan. No se alteró el parser ni funcionalidades de licencias de otros compañeros.

T004: legacy_preflight y comando acquisition_preflight solo leen. faculty_contract.py.txt es plantilla NO activa, probada en PostgreSQL temporal para aborto sin mapeo, VALIDATE y NOT NULL con datos verificados. No promoverla antes de revisar escritores legados 002; Asset.faculty sigue nullable en el modelo/grafo activos.

Los estados de secciones anteriores son históricos; la tabla final de tasks.md es el estado vigente.
