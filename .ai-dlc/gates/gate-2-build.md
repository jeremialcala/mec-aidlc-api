# Gate 2 — Build

Cierre de la Fase 03 (construcción, test-first). Marcar solo lo fundamentado (Human-in-the-Loop).

## Base heredada de Gate 1 (scaffold ya existente)
- [x] Estructura Clean/hexagonal (`domain` / `application` / `adapters` / `api`) — ADR-0004
- [x] Núcleo de scoring implementado y probado sin red (escala 1–4, IGV, estadio) — ADR-0006
- [x] Validación estricta de esquema (Pydantic `extra=forbid`, enteros 1–4) — A05
- [x] Verificación JWT Auth0 (RS256/JWKS, `iss`/`aud`/`exp`, `alg` fijado) + RBAC deny-by-default — ADR-0003
- [x] Manejo de errores sin fuga (A10) y logging de auditoría sin PII/secretos (A09)

## Brechas diseño↔código a cerrar (el diseño las promete; el scaffold aún no las realiza)
- [ ] **Reintento con backoff** idempotente en el adaptador Notion (timeout/429/5xx) — T6, A10
- [ ] **Idempotencia sin carrera TOCTOU**: `existe()`→`guardar()` no es atómico; garantizar
      unicidad efectiva por `(evaluado, fecha)` (verificación previa + manejo del duplicado) — T7, A08
- [ ] **Validación de existencia del evaluado** (escenario de abuso #5 del PRD): decidir el
      mecanismo sin violar el no-scope de personas → `<TODO humano: cómo validar la ficha>`
- [ ] `iss`/`aud` **obligatorios** en configuración de producción (hoy vacíos ⇒ no se validan) — T1/T3

## Pruebas (test-first, cobertura de abuso)
- [ ] Tests de **auth reales** (sin `AUTH_DISABLED`): 401 sin token / token inválido/expirado,
      403 por rol, claim de rol manipulado, `alg=none`, `aud`/`iss` incorrectos — PRD esc. 1,2,9
- [ ] Tests de **todos los escenarios de abuso** del PRD (1–9), incluidos payloads maliciosos
- [ ] Tests del adaptador Notion (reintento/backoff, 429/5xx → 502, no escribir campos fórmula)
- [x] Cobertura del núcleo de dominio **≥ 90 %** (100 %) verificada en CI (`--cov-fail-under=90`)

## Seguridad de la construcción (CI — A02/A03/A04)
- [ ] **Lockfile** de dependencias (pin exacto, incluye SDK/HTTP y libs JWT) — ADR-0005, A03
- [x] **SCA** de dependencias en CI (`pip-audit`) — A03
- [x] **Escaneo de secretos** en CI (`gitleaks`); falla si detecta secretos — A02/A04
- [x] **SAST / lint de seguridad** en CI (`ruff` reglas `S` + `bandit`)
- [x] Pipeline CI (`.github/workflows/ci.yml`): lint + SAST + tests + cobertura + SCA + secret scan
      — verificado en verde localmente; pendiente el primer run en GitHub
- [ ] TLS 1.2+ verificado de extremo a extremo (entrada y hacia Notion) — A04 (runtime/ops)

## Operación y cumplimiento (habilita la retención definida en Gate 0)
- [ ] Mecanismo/job de **retención**: purga o anonimización de resultados a *relación laboral + 2 años*
      y de logs de auditoría a *1 año* (operativo en Notion / plataforma de logs)
- [ ] Runbook mínimo de despliegue en servidor interno (variables, secretos, readiness `/health`)

## Confirmaciones humanas
- [ ] `<TODO humano>` Tenant Auth0 real configurado + Action que emite el claim de roles con namespace
- [ ] `<TODO humano>` Estrategia de purga de retención acordada con RRHH / plataforma

**Estado Gate 2: ABIERTO (preparado)** — criterios de aceptación definidos. El scaffold cubre
la base heredada de Gate 1; faltan las brechas diseño↔código, la batería completa de pruebas de
abuso/auth y los controles de seguridad de la construcción (SCA, secretos, SAST) en CI antes de
dar Gate 2 por cerrado.
