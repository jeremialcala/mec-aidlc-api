# ADR-0002: Notion como sistema de registro (sin base de datos propia)

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 02-design
- **Controles OWASP afectados:** A03 (supply chain), A04 (crypto), A08 (integridad), A10 (errores)

## Contexto
Los resultados ya viven en la BD Notion "Resultados Test MEC-AIDLC", con fórmulas que
derivan `Promedio D1–D4`, `IGV` y `Estadio`. El equipo consume y visualiza en Notion.
Requisito de `01-requirements/registro-resultados-evaluacion.md`.

## Decisión
Usar la **API de Notion como único sistema de registro**. La API escribe solo los campos
editables (16 competencias + `Evaluado` + `Fecha del test` + `Diagnóstico` + `Estado` +
`Resultado`); nunca los campos fórmula (solo lectura). No se mantiene copia local.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. Notion como registro | Cero duplicación, fórmulas ya existen, el equipo ya lo usa | Acoplamiento y SPOF a Notion; latencia de red | A03: dependencia de terceros; A10: manejar caídas |
| B. BD propia + sync a Notion | Control total, offline | Duplica fuente de verdad, complejidad de sync, más datos personales que custodiar | Más superficie (más PII almacenada) |

## Consecuencias
- Positivas: minimización de datos (no se replica PII), consistencia con las fórmulas.
- Negativas / deuda asumida: disponibilidad ligada a Notion; requiere manejo robusto de
  errores/reintentos (A10) y del token (A04, ver ADR-0005).
- Impacto en threat model: introduce T2 (token Notion) y T4 (dependencia externa).
