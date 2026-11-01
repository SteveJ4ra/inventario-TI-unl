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
- Datos existentes podrían no tener adquisición/facultad: migración no debe fabricar información. Completar con datos de prueba o una tarea de saneamiento autorizada.
- Una factura contiene conceptos no asignables: no imponer que suma de líneas sea igual al total de factura, pues impuestos/envío podrían diferir.