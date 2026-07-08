# ADR-0007: Integridad referencial del evaluado y modelo de alcance de acceso

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 03-build
- **Controles OWASP afectados:** A01 (access control), A05 (validación/insecure design)

## Contexto
Dos escenarios de abuso del PRD quedaban sin mecanismo definido porque exigían decisiones
de negocio: (#5) qué hacer si el `evaluado_id` no corresponde a una ficha real, y (#3) qué
alcance tiene un usuario al leer/registrar resultados de un evaluado. El charter declara la
**gestión** del catálogo de personas como *no-scope* (vive en la BD "Equipo de Desarrollo —
Fichas"); esto no impide **leer** ese padrón para validar integridad.

## Decisión
- **#5 — Validación del evaluado (integridad referencial):** antes de registrar, la API
  **verifica que el `evaluado_id` exista en la BD 'Fichas'** consultando esa data source en
  modo **solo lectura** (recupera la página y comprueba que su `parent` sea la BD de fichas).
  Si no existe → **422**, sin crear página huérfana. Es lectura, no gestión: no viola el
  no-scope. Se configura con `NOTION_FICHAS_DATA_SOURCE_ID`; si está vacío, la validación se
  omite (dev/local) — **debe** configurarse en producción.
- **#3 — Alcance de acceso: control por rol, sin alcance por evaluado.** Cualquier usuario
  autenticado con rol `evaluador` (escritura) o `lector` (lectura) puede operar sobre
  **cualquier** evaluado. El control de acceso es el **rol** (RBAC deny-by-default, ADR-0003)
  más la **auditoría** por usuario (A09) y la minimización de datos (ADR-0002). No se modela
  alcance por evaluado/equipo. En consecuencia, el escenario #3 del PRD se **retira** como
  requisito y se sustituye por esta política explícita.

## Alternativas consideradas
| Decisión | Opción elegida | Alternativas descartadas | Motivo |
|---|---|---|---|
| #5 | Consultar BD Fichas (solo lectura) | (b) confiar en el 400 de Notion por relación inválida; (c) no validar | (b) menos explícito y dependiente del comportamiento de Notion; (c) admite páginas con relación inválida |
| #3 | Control por rol | (b) alcance por quién registró (`sub`); (c) alcance por equipo (claim/Fichas) | Equipo interno único; el rol + auditoría + minimización bastan; (b)/(c) añaden complejidad sin necesidad clara |

## Consecuencias
- Positivas: se cierra #5 con un 422 explícito y trazable; el modelo de acceso #3 queda simple
  y documentado, coherente con el despliegue interno de un solo equipo.
- Negativas / deuda asumida: la validación de #5 añade una llamada de lectura a Notion por
  registro y acopla (solo lectura) a la BD de fichas; el acceso por rol **no** aplica menor
  privilegio por evaluado — si a futuro se requiere, se revisará hacia la alternativa (b)/(c).
- Impacto en threat model: refuerza A05 (integridad de entrada) y mantiene A01 en el rol.
