# MEC-AIDLC API

Repositorio AI-DLC del servicio que registra resultados de la evaluación **MEC-AIDLC** en
la base de datos Notion *Resultados Test MEC-AIDLC*. Generado hasta **Gate 1** (fases 0, 1 y 2).

## Estructura
```
docs/
  00-project/     charter, glosario, clasificación de datos, ADRs (0001–0007)
  01-requirements/ PRD con escenarios de abuso + requisitos OWASP ASVS
  02-design/      arquitectura, threat model STRIDE/DREAD, contrato de API
  architecture/   diagramas C4 (Context + Container, Mermaid)
.ai-dlc/
  templates/      plantillas prd / threat-model / adr
  gates/          checklists Gate 0, Gate 1 y Gate 2
apps/
  mec-aidlc-api/  servicio FastAPI (Clean Architecture) + tests
```

## Metodología
AI-DLC: seguridad por diseño, test-first, principios sobre frameworks, Human-in-the-Loop.
Regulación de datos: Ley 1581 (Colombia) / LFPDPPP (México).

## Estado de gates
- **Gate 0 (Requirements):** ✅ **cerrado** — responsable de datos (RRHH), autorización vía
  aviso de privacidad en onboarding, retención (resultados = relación laboral + 2 años; logs = 1 año).
- **Gate 1 (Design):** ✅ **cerrado** — escala/umbrales 1–4 (ADR-0006), IdP **Auth0** con
  tokens de 60 min y rotación de secretos de 7 días (ADR-0003/0005). Ver `.ai-dlc/gates/`.
- **Gate 2 (Build):** 🚧 **abierto** — criterios de aceptación definidos (brechas diseño↔código,
  pruebas de abuso/auth, SCA/secretos/SAST en CI, retención operativa). Ver `.ai-dlc/gates/gate-2-build.md`.

## Arrancar el servicio
Ver `apps/mec-aidlc-api/README.md`.
