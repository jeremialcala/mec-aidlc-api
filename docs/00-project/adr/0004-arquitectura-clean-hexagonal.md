# ADR-0004: Clean Architecture / puertos y adaptadores

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 02-design
- **Controles OWASP afectados:** A06 (insecure design)

## Contexto
El cálculo de IGV, estadio y patrón diagnóstico es la lógica de negocio central y debe ser
reproducible, testeable y desacoplada tanto de FastAPI como de Notion (que podría cambiar).

## Decisión
Estructurar el servicio en capas Clean/hexagonal:
- `domain/` — entidades, value objects y **scoring** (IGV, estadio, patrón). Sin dependencias externas.
- `application/` — casos de uso y **puertos** (protocolos como `ResultRepository`).
- `adapters/` — infraestructura: `NotionResultRepository`, verificación JWT.
- `api/` — FastAPI: routers, esquemas Pydantic, inyección de dependencias.
Regla de dependencia: `api → application → domain`; `adapters` implementa puertos de `application`.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. Clean/hexagonal | Dominio testeable, Notion intercambiable, límites claros | Más archivos/ceremonia | Bajo (diseño seguro) |
| B. Todo en routers FastAPI | Rápido | Lógica acoplada a I/O, difícil de testear | A06: diseño frágil |

## Consecuencias
- Positivas: el scoring se prueba sin red; el adaptador de Notion se sustituye por un fake en tests.
- Negativas / deuda asumida: mayor estructura inicial.
- Impacto en threat model: aísla la validación de entrada (api) del núcleo (domain).
