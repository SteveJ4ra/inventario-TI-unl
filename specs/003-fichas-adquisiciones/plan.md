# Plan: administración de fichas y adquisición

**Rama propuesta:** feature/administracion-fichas-adquisiciones
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
