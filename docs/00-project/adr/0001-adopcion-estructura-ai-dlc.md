# ADR-0001: Adopción de la estructura de repositorio AI-DLC

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 00-project
- **Controles OWASP afectados:** transversal

## Contexto
El proyecto debe seguir la metodología AI-DLC (seguridad por diseño, test-first,
principios sobre frameworks, Human-in-the-Loop) con fases y gates explícitos.

## Decisión
Adoptar la estructura estándar AI-DLC (`docs/00-project`, `01-requirements`, `02-design`,
`.ai-dlc/gates`, `.ai-dlc/templates`, `apps/<servicio>`) y cerrar hasta Gate 1 en el bootstrap.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. Estructura AI-DLC | Trazabilidad, gates, seguridad por diseño | Overhead documental inicial | Bajo |
| B. Repo FastAPI plano | Arranque rápido | Sin threat model ni gates | Alto (seguridad como parche) |

## Consecuencias
- Positivas: diseño trazable a OWASP y a Alles; gates verificables.
- Negativas / deuda asumida: mantener docs sincronizadas con el código.
- Impacto en threat model: habilita el modelo STRIDE/DREAD de la Fase 02.
