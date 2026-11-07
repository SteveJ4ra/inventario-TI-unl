# Identificación y clasificación de actores

**Proyecto:** Inventario de Tecnologías de Información · Grupo N.º 5 · Universidad Nacional de Loja
**Sección:** identificación de actores · **Responsable:** Emilio

## 1. Contexto del proyecto

El proyecto proviene del portafolio remitido por DTI. La necesidad es gestionar la información de los activos tecnológicos, su ubicación, su responsable o custodio, su estado y sus movimientos, de manera que pueda conocerse su situación actual y parte de su historial.

El reto consiste en diferenciar el registro de un activo de los eventos que ocurren durante su ciclo de vida: asignaciones, cambios de ubicación, mantenimiento, novedades o baja.

## 2. Alcance considerado para los actores

El enunciado plantea como preguntas para explorar el uso de un código QR en el inventario físico y la consulta desde dispositivos móviles. Para el alcance inicial se optó por un sistema más simple, por lo que ambos aspectos quedan fuera y podrían incorporarse en una etapa posterior. Esta decisión debe confirmarse con el equipo y con el docente o DTI.

## 3. Actores identificados y clasificación

A partir del enunciado se identificaron tres actores que interactúan con el sistema, clasificados así:

- **Usuario principal:** gestor de activos, quien registra y modifica la información.
- **Usuario secundario:** custodio, quien consulta y confirma lo que tiene a cargo.
- **Responsable del sistema:** administrador, quien controla los accesos y supervisa el sistema.

No se identificó ningún actor externo ni sistema o servicio relacionado en el alcance inicial (ver sección 7).

## 4. Mapa de actores

El mapa en formato Mermaid está en [mapa-actores.md](mapa-actores.md).

## 5. Descripción de los actores

| Actor y clasificación | Necesidad o interés | Interacción esperada | Información que proporciona / consulta | Restricciones o condiciones |
|---|---|---|---|---|
| **Gestor de activos** (usuario principal) | Registro confiable de cada activo, su ubicación, custodio y estado. | Registra y modifica la ficha del activo; registra asignaciones, traslados, mantenimientos, novedades y bajas; verifica el inventario. | Proporciona los datos del activo y de sus eventos. Consulta el historial. | Solo personal autorizado de DTI (por confirmar). Todo cambio debe quedar en el historial. |
| **Custodio** (usuario secundario) | Saber qué activos tiene a cargo y en qué estado se encuentran. | Consulta sus activos, confirma la recepción y reporta novedades. | Proporciona confirmaciones y novedades. Consulta lo que tiene asignado. | Solo ve sus propios activos y no modifica la ficha (por confirmar). |
| **Administrador** (responsable del sistema) | Controlar los accesos, mantener los catálogos y tener una visión general. | Gestiona usuarios, roles y catálogos. Consulta reportes. | Proporciona usuarios, roles y catálogos. Consulta reportes e historial. | No debería alterar el historial de movimientos (por confirmar). |

> **Nota:** lo marcado como "por confirmar" es un supuesto del equipo que debe validarse con DTI o con el docente; no corresponde a una política institucional aprobada.

## 6. Interacciones principales

- El gestor registra el activo y sus eventos (asignación, traslado, mantenimiento, novedad y baja) y lo asigna al custodio.
- El custodio consulta lo que tiene a cargo, confirma la recepción y reporta novedades.
- El administrador gestiona usuarios, roles y catálogos, y consulta reportes.

## 7. Actores considerados y descartados

También se consideraron el auditor, el técnico de soporte, el responsable de DTI, el proveedor y un servicio de autenticación institucional. El auditor existía para verificar el inventario físico con QR, por lo que sale junto con ese aspecto y su función la asume el gestor. El técnico se integró en el rol del gestor (registro de mantenimientos y novedades) y el responsable de DTI en el del administrador (supervisión y reportes). El proveedor y la autenticación institucional quedaron fuera por no aparecer en el enunciado; podrían incorporarse si DTI lo requiere.

## 8. Preguntas de clarificación sobre los actores

1. ¿Quiénes registran activos en DTI (cuántas personas y con qué cargos)?
2. ¿Los custodios tendrán cuenta propia en el sistema, o solo se registra lo que ellos confirman?
3. ¿Quién puede dar de baja un activo y se requiere la aprobación de otra persona?
4. ¿Existe un sistema institucional de usuarios o un inventario previo con el que deba integrarse?
5. ¿El uso de QR y la consulta móvil quedan fuera del alcance inicial, o DTI espera que se incluyan?

## 9. Fuentes y declaración de uso de IA

- Enunciado del proyecto de inventario de activos tecnológicos, portafolio remitido por DTI.
- Guía de la actividad autónoma AA1 (análisis de actores y fundamentos de SDD).
- **Declaración de uso de IA:** se utilizó Claude (Anthropic) como apoyo para estructurar la tabla de actores y elaborar el mapa; el contenido fue revisado por el estudiante.
