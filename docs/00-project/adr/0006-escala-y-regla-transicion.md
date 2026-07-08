# ADR-0006: Escala de competencias y regla de transición de estadio

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 02-design
- **Controles OWASP afectados:** A06 (insecure design — consistencia de reglas)

## Contexto
El IGV y el estadio dependen de (a) la **escala numérica** de las 16 competencias y (b) los
**umbrales por dominio** de la regla de transición. Estos valores deben coincidir con la
herramienta HTML existente y con las fórmulas de Notion para no producir resultados divergentes.
No están confirmados en la descripción; rellenarlos "a ciegas" viola el principio de no inventar.

## Decisión (confirmada — Jeremi, 2026-07-08)
- **Escala:** cada ítem es un **entero 1–4** anclado en los grados Alles: **A=4** (referente),
  **B=3** (sólido y autónomo), **C=2** (funcional con apoyo), **D=1** (mínimo desarrollado).
- **Promedio por dominio:** media de sus 4 ítems → también en rango [1, 4].
- **IGV:** `0.20·D̄1 + 0.30·D̄2 + 0.30·D̄3 + 0.20·D̄4`, en escala 1–4 (marco MEC-AIDLC).
- **Normalización a porcentaje (lineal):** `%IGV = (IGV − 1) / 3 × 100`
  (1.00 = 0 %, 2.00 ≈ 33 %, 2.50 = 50 %, 3.00 ≈ 67 %, 4.00 = 100 %).
- **Regla de transición por umbrales (no promedio simple), pivote 3.00 = grado B:**
  - **Generador de Valor:** IGV ≥ 3.0 **y** D̄2 ≥ 3.0 **y** D̄3 ≥ 3.0 **y** D̄1 ≥ 2.4 **y** D̄4 ≥ 2.4.
  - **Team Player:** D̄3 ≥ 2.4 **y** D̄1 ≥ 2.0 (colabora con base técnica suficiente).
  - **Contribuidor Individual:** cualquier otro caso.

Los valores viven centralizados en `domain/scoring.py` (constantes) para ajuste trivial.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. Umbrales por dominio | Evita que un dominio alto enmascare déficits; alineado al marco | Requiere calibración | Bajo |
| B. Promedio simple / IGV solo | Simple | Un dominio fuerte oculta uno crítico; contradice el marco | Diagnóstico erróneo |

## Consecuencias
- Positivas: regla explícita, testeable y trazable al marco; escala y umbrales confirmados.
- Negativas / deuda asumida: los umbrales secundarios (D̄1/D̄4 ≥ 2.4, TP D̄1 ≥ 2.0) deben
  mantenerse en sincronía con las fórmulas de Notion y la herramienta HTML si estas cambian.
- Impacto en threat model: N/A directo; afecta la corrección del resultado, no la seguridad.
