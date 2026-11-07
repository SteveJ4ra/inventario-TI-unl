    # Especificación DEMOSTRATIVA — Inventario de TI

**Estado: BORRADOR PEDAGÓGICO — no constituye especificación aprobada ni salida verificada de `/speckit.specify`.**

Este documento muestra cómo organizar el **qué** del sistema. Los elementos marcados **PROPUESTO** no deben convertirse en requisitos formales hasta que el equipo o requirente los confirme.

## 1. Contexto y problema

Según el banco ACD1, se requiere gestionar información de activos tecnológicos, su ubicación, custodio o responsable, estado y movimientos para conocer su situación actual y parte de su historial. La dificultad central es distinguir el registro del activo de sus eventos de ciclo de vida.

## 2. Objetivo inicial (PROP)

Facilitar la consulta consistente de la situación de cada activo TI y la comprensión de sus movimientos relevantes, según las reglas que valide el requirente.

## 3. Alcance preliminar

No está aprobado el primer incremento. **Ejemplo de subconjunto para practicar:** información básica de activos y consulta de situación actual. **No afirmarlo como alcance institucional**.

## 4. Fuera de alcance 

No se conoce todavía; no excluir QR, exportaciones, móvil, mantenimiento o baja como decisión definitiva. Son puntos a deliberar.

## 5. Actores 

El banco menciona la noción de responsable/custodio, pero aún no define perfiles, privilegios ni procesos de aprobación. Evitar crear actores «administrador», «técnico» o «auditor» como roles confirmados.

## 6. Escenario ilustrativo — PROPUESTO, NO APROBADO

**EU-P01:** Como persona **autorizada para consultar inventario** (rol por confirmar), quisiera consultar la situación de un activo tecnológico para conocer su ubicación, estado y custodio, si estos datos se encuentran disponibles y se permite su consulta.

## 7. Requisitos funcionales candidatos — PENDIENTES

| Código provisional | Propuesta | Pregunta para validar |
|---|---|---|
| RF-P01 | Consultar la información actual de un activo | ¿Quién puede consultar y por qué identificador? |
| RF-P02 | Registrar o actualizar información del activo | ¿Quién puede crear o modificar, y cuáles campos son obligatorios? |
| RF-P03 | Consultar movimientos de un activo | ¿Qué eventos se consideran movimientos y cuánto historial se conserva? |

**No son requisitos aprobados.** La ficha académica describe el dominio, no impone aquí estas operaciones completas.

## 8. Requisitos no funcionales — a medir tras clarificación

- Seguridad y privacidad acordes a la clasificación real de la información.
- Calidad de datos, consistencia y trazabilidad según reglas reales del dominio.
- Facilidad para probar y mantener la implementación (objetivo de ingeniería del grupo).
- NO inventar latencias, porcentajes ni volúmenes de usuarios.

## 9. Reglas de negocio

RB-P01: Identificador único del activo: **sin definir**.  
RB-P02: Condiciones para una asignación/cambio de custodio: **sin definir**.  
RB-P03: Estados y transición hacia «baja»: **sin definir**.

## 10. Datos y estados relevantes

Conceptos observables: **activo, ubicación, custodio/responsable, estado y movimiento**. No implica todavía cinco tablas ni relaciones 1:N específicas. Tipos de movimiento mencionados como ejemplos en el banco: asignación, cambio de ubicación, mantenimiento, novedades y baja.

## 11. Criterios de aceptación — EJEMPLO CONDICIONAL

**CA-P01 (borrador, asociado a RF-P01):**  
**Dado** que existe un activo de ejemplo y una persona con permisos de consulta **por definir**,  
**Cuando** solicita consultar ese activo,  
**Entonces** recibe los datos de situación actual autorizados conforme al alcance aprobado.  
**Observación:** necesita definir actor, identificador y campos para ser plenamente verificable.

## 12. Casos límite / errores que debemos discutir

Activo inexistente; identificador duplicado; registro sin custodio; cambios simultáneos; movimiento no permitido; inconsistencia entre estado actual e historial. **Son casos a investigar, no reglas ya definidas.**

## 13. Dependencias

- Acuerdos ACD1 del equipo; posibles políticas institucionales; respuesta del requirente.
- Confirmación de recursos técnicos y stack por Alex.

## 14. Supuestos NO CONFIRMADOS

El sistema probablemente tendrá usuarios con acceso diferenciado y un identificador de activo, pero no se conoce su forma concreta. Estos supuestos **no deben tratarse como requisitos**.

## 15. Preguntas abiertas

Consultar `03_CLARIFICACIONES_PENDIENTES.md`.

## 16. Trazabilidad inicial

| Necesidad fuente | Propuesta de requisito | Aceptación | Estado |
|---|---|---|---|
| Conocer situación actual de un activo (Banco ACD1 p. 3) | RF-P01 | CA-P01 | PROPUESTA; esperando validación |
| Comprender parte del historial del activo (Banco ACD1 p. 3) | RF-P03 | Pendiente | PROPUESTA; esperando validación |

## Validación requerida antes de implementar

- [ ] Yandri confirma alcance y exclusiones.
- [ ] Emilio valida actores y permisos por conocer.
- [ ] Pedro entrega preguntas y, si existen, respuestas justificadas.
- [ ] Alex confirma restricciones tecnológicas y características relevantes.
- [ ] Requirente/docente resuelve dudas que afecten reglas y alcance.
