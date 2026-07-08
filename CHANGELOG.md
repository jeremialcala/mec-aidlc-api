# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog 1.1.0](https://keepachangelog.com/es/1.1.0/)
y el proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- Reintento con backoff exponencial (honra `Retry-After`) e idempotencia de creación en el
  adaptador Notion: ante un fallo transitorio re-verifica por (evaluado, fecha) antes de
  reintentar, para no duplicar — T6/T7, A08/A10.
- Lock por `(evaluado, fecha)` en el caso de uso que cierra la carrera TOCTOU entre la
  verificación de existencia y el guardado (`application/concurrency.py`) — A08.
- Parámetros de reintento configurables: `NOTION_MAX_REINTENTOS`, `NOTION_BACKOFF_BASE_S`,
  `NOTION_BACKOFF_MAX_S`.
- Tests: adaptador Notion (reintento/idempotencia/lectura), concurrencia TOCTOU y verificación JWT.

### Seguridad
- Verificación JWT endurecida: `iss` y `aud` **obligatorios** con JWKS (fail-closed) y `require`
  de `exp`/`iss`/`aud`; rechazo de `alg=none` verificado con test — T1/T3.

## [0.1.0] - 2026-07-08

Bootstrap AI-DLC del servicio, cerrado hasta Gate 1 (diseño). Gate 0 y Gate 1 superados.

### Añadido
- Estructura de repositorio AI-DLC (fases 00–02, `.ai-dlc/gates`, plantillas) — ADR-0001.
- Núcleo de dominio: scoring MEC-AIDLC (promedios D1–D4, IGV, estadio y patrón diagnóstico)
  en escala entera **1–4** (grados Alles A=4, B=3, C=2, D=1), reproducible y probado sin red — ADR-0006.
- Normalización del IGV a porcentaje: `(IGV − 1) / 3 × 100`.
- API FastAPI: `POST /v1/resultados`, `GET /v1/resultados`, `GET /health`; validación estricta
  de esquema (Pydantic `extra=forbid`, enteros 1–4).
- Persistencia en Notion escribiendo solo campos editables (nunca los campos fórmula) — ADR-0002.
- Autenticación OAuth2 + JWT con **Auth0** (RS256/JWKS, `iss`/`aud`/`exp`) y RBAC deny-by-default;
  roles desde claim con namespace o `permissions` — ADR-0003.
- Pipeline de CI (GitHub Actions): ruff (lint + reglas de seguridad), bandit (SAST), pytest con
  cobertura del dominio ≥ 90 %, pip-audit (SCA) y gitleaks (escaneo de secretos).
- Este CHANGELOG (formato Keep a Changelog 1.1.0).

### Seguridad
- Validación de firma, `iss`, `aud` y `exp` con algoritmos fijados (mitiga `alg=none`) — amenazas T1/T3.
- Gestión de secretos solo por entorno; rotación cada 7 días; TLS 1.2+ — ADR-0005.
- Manejo de errores sin fuga de detalles internos (A10) y logging de auditoría sin PII/secretos (A09).
- Clasificación de datos y cumplimiento Ley 1581 / LFPDPPP (responsable, autorización del titular
  y política de retención) — Gate 0.

<!-- Enlaces de comparación: añadir cuando el repositorio tenga remoto en GitHub, p. ej.
[Unreleased]: https://github.com/<owner>/<repo>/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<owner>/<repo>/releases/tag/v0.1.0 -->
