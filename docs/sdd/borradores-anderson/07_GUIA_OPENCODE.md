# Práctica guiada: GitHub Spec Kit + OpenCode en Ubuntu

**Tu instalación ya se observó en funcionamiento.** No reinstalar ni ejecutar de nuevo `specify init` en `~/inventario-ti-practica`; el aviso «Directory already exists» no era un error de la instalación.

## 0. Inspección sin modificar archivos

En una terminal:

```bash
cd ~/inventario-ti-practica
pwd
specify version
ls -la .specify
ls -la .opencode/commands
cat .specify/memory/constitution.md
```

**Por qué:** conocer el estado actual antes de pedir cambios al agente.

## 1. Revisar la constitución existente (PRIMERO)

Tu `constitution.md` actual afirma que está ratificada `1.0.0`, impone TDD y contiene reglas que no fueron aprobadas. En OpenCode (abierto desde `~/inventario-ti-practica`) utiliza un **mensaje normal** antes de ejecutar cualquier otro comando:

> Analiza únicamente `.specify/memory/constitution.md`. El único problema confirmado es el definido en el banco de proyectos: activos tecnológicos, ubicación, custodio, estado y movimientos. Identifica afirmaciones asumidas, como TDD obligatorio, permisos, retención y versión ratificada. Propón correcciones sin cambiar requisitos ni avanzar de etapa. Señala claramente lo no aprobado y pide aprobación antes de editar.

Después de revisar el resultado, autoriza **solo cambios fundamentados**. No podemos afirmar que ya fueron hechos.

## 2. Practicar `specify` sin inventar datos

Una vez revisada la constitución, en el chat de OpenCode (NO en Bash):

```text
/speckit.specify Preparar una especificación inicial DEMOSTRATIVA del proyecto Inventario de TI. Hechos confirmados: el banco ACD1 exige considerar activos tecnológicos, ubicación, responsable/custodio, estado y movimientos e identificar eventos de ciclo de vida. NO hay alcance, actores, identificadores, reglas de autorización ni stack confirmados. Diferencia HECHOS, PROPUESTAS y PREGUNTAS ABIERTAS. No inventes respuestas del requirente ni decisiones de compañeros. Para el ejemplo considera como funcionalidad CANDIDATA la consulta de la situación actual de un activo, pendiente de validación. No implementes código.
```

**Revisar qué creó el agente**: consultar la ruta que informe y abrir `spec.md` si lo creó. Según versión puede usar `specs/<feature>/spec.md` y registrar la característica activa en `.specify/feature.json`. No inventar rutas exactas si no coinciden con tu entorno.

## 3. Practicar `clarify`

En OpenCode:

```text
/speckit.clarify Identifica dudas sobre identificadores, usuarios, permisos, custodios, ubicación, estados, movimientos e historial del inventario. NO contestes automáticamente ni asumas políticas. Lista las preguntas bloqueantes y señala cuáles requieren al requirente o los acuerdos del equipo. Si necesitas respuestas para modificar la especificación, detente y solicita confirmación.
```

**Por qué:** la guía docente distingue clarificación de invención de reglas de negocio.

## 4. Plan y tasks: no fingir que están completos

Aún no existe una selección tecnológica aprobada por Alex ni especificación validada. **No es correcto generar un `plan.md` y `tasks.md` técnicos finales como si ya hubieran elegido un framework**. En APE1 sí debes mostrar que conoces su función y que la estructura inicial los contempla. Una vez recibidos los acuerdos, usar:

```text
/speckit.plan [Describir stack, restricciones, arquitectura y decisiones APROBADAS]
/speckit.tasks
```

Nunca escribir los corchetes literalmente esperando un plan válido: sustitúyelos por decisiones reales. `tasks` depende del plan revisado. Puedes mostrar los borradores `04_...` y `05_...` como evidencia de preparación, claramente separados de las salidas reales del agente.

## 5. Guardar evidencia y contribución

Cuando Steven confirme repositorio y rama de trabajo, seguir su estrategia. **No usar `git init` ni `git push` indiscriminadamente en el repositorio grupal**. Ejemplos locales de inspección Git (si ya existe Git):

```bash
git status
git branch --show-current
git log --oneline -5
```

Si necesitas guardar registro de la práctica, añade a tu documento fecha, comando, propósito, resultado observado, capturas reales, errores y correcciones. No hacer pasar archivos preparados con ChatGPT por archivos generados automáticamente por Spec Kit.

## ¿Cómo usar SOLID/POO aquí?

- **Ahora, Constitución:** declarar principios de calidad, bajo acoplamiento, responsabilidades claras, limpieza de código y SOLID cuando corresponda.
- **Luego, Especificación:** NO poner frameworks, clases ni SQL para explicar lo que el sistema debe permitir.
- **Luego, Plan:** decidir estructura de clases, paquetes/capas, interfaces, inyección de dependencias si resulta útil, tras acordar el stack.
- **Luego, Tasks:** tareas pequeñas derivadas del plan y vinculadas a criterios de aceptación.

## Diferencia entre prototipo de aprendizaje y entrega real

Esta guía y los archivos adjuntos son material didáctico. La **APE1 real** exige repositorio compartido, ramas, README, estructura SDD, alcance y stack preliminar justificado, con evidencias individuales. Los otros responsables completarán sus partes antes de consolidar los tres productos.
