# Gate 1 — Design

Cierre de la Fase 02. Marcar solo lo fundamentado (Human-in-the-Loop).

- [x] Arquitectura definida (Clean/hexagonal) — `02-design/architecture.md`
- [x] Diagrama C4 (Context + Container) con trust boundaries — `docs/architecture/`
- [x] Threat model STRIDE del sistema — `02-design/threat-model.md`
- [x] Amenazas priorizadas con DREAD (T1–T8), cada una trazada a control OWASP/ADR
- [x] ADRs de decisiones clave — `docs/00-project/adr/` (0001–0006)
- [x] Contratos de API (endpoints + esquemas) — `02-design/api-contract.md`
- [x] Patrones de seguridad por amenaza priorizada — tabla en `architecture.md`
- [x] Escala numérica (entero 1–4, grados Alles) y umbrales de transición confirmados — ADR-0006 (accepted)
- [x] IdP confirmado: **Auth0** (RS256/JWKS, `iss`/`aud`/`exp`), token **60 min**, rotación de secretos **7 días** — ADR-0003/0005

**Estado Gate 1: CERRADO** — todas las decisiones de diseño están confirmadas y trazadas.
Auth0 como IdP (validación de firma/`iss`/`aud`/`exp`, roles vía claim con namespace, tokens
de 60 min), rotación de secretos bajo nuestro control cada 7 días, y escala/umbrales 1–4
reflejados en `domain/scoring.py` y tests. Diseño completo, ejecutable y validado por humano.
