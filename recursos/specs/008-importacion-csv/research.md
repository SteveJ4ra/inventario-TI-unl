# Research: importación CSV

| Tema | Decisión | Razón |
|---|---|---|
| Atomicidad | Validar primero y aplicar todo en una única transacción | Cumple todo-o-nada y evita inventario parcial. |
| Formatos | CSV separado por dominio y versión de plantilla | Los activos y lotes tienen campos/validaciones distintos. |
| Confirmación | Preview inmutable y dos pasos ligados a su hash/id | Evita confirmar silenciosamente otro contenido. |
| Reglas | Reutilizar modelos/servicios de 003 y 006 | Mantiene misma validación manual e importada. |
| Límites técnicos | Definir tamaño/filas antes de habilitar | Mitiga consumo de memoria/abuso; exceder límite rechaza todo. |

No se incluye adaptación a Excel, integración externa ni reglas institucionales de archivo.
