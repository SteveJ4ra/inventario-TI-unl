# Plan técnico — esquema PENDIENTE (no `plan.md` definitivo)

**No debe presentarse como producto real generado por `/speckit.plan`.** Se completará cuando haya especificación y decisión tecnológica validadas.

## Información aún necesaria

- [ ] Alcance y requisitos priorizados (Yandri + equipo).
- [ ] Actores y permisos (Emilio + requirente).
- [ ] Clarificaciones resueltas (Pedro + requirente).
- [ ] Stack backend elegido con criterios (Alex + equipo).
- [ ] Repositorio y estrategia de ramas (Steven).

## Decisiones de diseño para DISCUTIR, no para afirmar como implementadas

**Alternativa educativa:** organización por responsabilidades con separación de interfaz HTTP, casos de uso/reglas del dominio y acceso a datos. Puede ser monolito modular u otro enfoque razonado; no se ha seleccionado arquitectura. Se deben discutir costo, complejidad, mantenibilidad y tiempo de curso.

### POO / SOLID / Clean Code — cómo evaluar su aplicación

| Idea | Aplicación sugerida, si el backend elegido es OO | Qué evitar |
|---|---|---|
| Encapsulación (POO) | Proteger invariantes validadas del activo en objetos de dominio | Clases sin reglas solo por aparentar POO |
| SRP | Separar validación del dominio, exposición HTTP y persistencia | Una clase que valide, guarde y responda HTTP |
| OCP | Extender comportamientos cuando surja una variación real | Crear patrones por cambios imaginarios |
| LSP | Diseñar sustituciones coherentes si se usan herencia/interfaces | Jerarquías artificiales sin necesidad |
| ISP | Interfaces pequeñas según consumidores reales | Mega interfaces generales |
| DIP | Casos de uso dependientes de contratos de persistencia si aportan valor | Multiplicar interfaces sin beneficio |
| Clean Code | Nombres del dominio claros, funciones pequeñas por cohesión, pruebas y manejo explícito de errores | Métricas rígidas arbitrarias o código complejo disfrazado |

**Nota:** SOLID son principios de diseño para código OO, no equivalentes a requisitos funcionales ni garantía automática de calidad. POO es una decisión de enfoque, no necesariamente obligación del sílabo.

## Datos conceptuales (no base de datos)

El banco oficial menciona activo, ubicación, responsable/custodio, estado y eventos de movimiento. Las entidades físicas, cardinalidades, campos e índices se decidirán al confirmar reglas de negocio.

## Contrato API REST (posterior)

El sílabo prevé API RESTful y OpenAPI en semanas posteriores. **No crear rutas, verbos y payloads inventados como contrato actual**. Cuando existan requisitos definidos, proponer recursos y respuestas y revisar validaciones.

## Calidad y seguridad

- Vincular requisitos validados con criterios de aceptación y pruebas.
- Proteger secretos; analizar acceso, permisos y exposición de datos según reglas conocidas.
- Documentar riesgos técnicos identificados por Alex, no inventar probabilidades.
- Anotar estrategia de pruebas acordada (unitarias/integración/aceptación); TDD solo si el grupo lo decide.

## Estado

**PLAN TÉCNICO DETALLADO: BLOQUEADO POR DECISIONES PENDIENTES**. Esto no impide presentar el flujo SDD en ACD/AA o mostrar la estructura inicial en APE.
