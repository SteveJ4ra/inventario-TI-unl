# Constitución PROPUESTA — Proyecto Inventario de TI

> Propósito: definir principios transversales de ingeniería. Esta constitución no decide qué funcionalidades institucionales son obligatorias ni selecciona frameworks.

## Principios

### I. Comprensión y trazabilidad de requisitos

Toda funcionalidad propuesta deberá tener relación identificable con una necesidad del dominio, un requisito o un criterio de aceptación. Las dudas importantes se registrarán antes de tomar decisiones irreversibles. Los cambios deberán actualizar la documentación afectada.  
**Razón:** El inventario debe reflejar necesidades reales, no supuestos del programador.

### II. Integridad y calidad de la información

El diseño debe preservar la consistencia de la información y permitir detectar datos inválidos o contradictorios. Las reglas concretas de identificación, custodia, baja, historial y conservación de datos **siguen pendientes de clarificación**.  
**Razón:** Una ficha actual del activo y sus movimientos no deberían contradecirse.

### III. Seguridad, privacidad y acceso responsable

Se aplicarán controles proporcionales a los datos, usuarios y acciones que resulten confirmados. No se publicarán credenciales ni secretos en el repositorio; el acceso a cambios sensibles deberá justificarse a partir de roles validados.  
**Razón:** Un inventario puede contener información sensible sobre infraestructura y custodios.

### IV. Calidad verificable, Clean Code y SOLID cuando corresponda

Las funcionalidades implementadas deberán tener criterios de aceptación y pruebas acordes a su riesgo. Se favorecerán nombres claros, funciones con responsabilidades comprensibles, bajo acoplamiento y revisión por pares. En componentes orientados a objetos se procurará aplicar **SOLID** y encapsulación, evitando capas o abstracciones sin necesidad. **No se impone TDD como requisito**, salvo decisión posterior del grupo.  
**Razón:** La calidad y mantenibilidad deben ser comprobables, no solo declaradas.

### V. Simplicidad, colaboración y evolución controlada

El trabajo se limitará al alcance validado. Los cambios en Git deberán ser rastreables, revisables y documentados. Toda nueva dependencia o servicio técnico requerirá una justificación relacionada con el problema o los requisitos.  
**Razón:** El sistema debe poder crecer por incrementos backend, frontend y móvil sin sobreingeniería.

## Restricciones generales de trabajo — propuestas

- Distinguir el **qué y por qué** de `spec.md` del **cómo** de `plan.md`.
- Mantener referencias entre necesidad → requisito → aceptación → diseño → tarea → prueba a medida que existan los artefactos.
- Registrar evidencia de contribuciones individuales en Git o en documento equivalente.
- Documentar limitaciones, decisiones pendientes, fuentes y participación de IA.
- Mantener el proyecto reproducible mediante un README, responsabilidad liderada por Steven.

## Gobernanza — propuesta

1. La constitución pasará a **VALIDADA** solamente después de una revisión conjunta y el registro de la aprobación del equipo.
2. Los principios podrán cambiar con una razón documentada.
3. Los detalles de arquitectura, stack, esquemas, endpoints y roles precisos se decidirán en su etapa y documento correspondiente.
4. Antes de programar, confrontar cada especificación y plan con estos principios.

## Pendientes de revisión del equipo

- [ ] Confirmar si POO será un enfoque del backend y en qué capas.
- [ ] Confirmar la estrategia de pruebas y el uso o no de TDD.
- [ ] Ajustar exigencias de seguridad a las políticas y usuarios reales.
- [ ] Revisar si hay requisitos del docente no incorporados.
- [ ] Registrar responsables y fecha de ratificación; solo entonces asignar versión estable.

**Autor del borrador:** Anderson, con asistencia de IA. **Aprobación:** pendiente.
