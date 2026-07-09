# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog 1.1.0](https://keepachangelog.com/es/1.1.0/)
y el proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Corregido
- `Notion-Version` por defecto (`2022-06-28`) no soportaba los endpoints/parent de *data sources*
  que usa el adaptador → la integración real fallaría; se fija a `2025-09-03`. Añadidos tests de
  contrato (ruta `/data_sources/{id}/query`, parent `data_source_id`, header de versión).
- El verificador JWT (`PyJWKClient`) se recreaba en cada petición, sin reutilizar la caché de JWKS;
  ahora se crea una sola vez en el `lifespan` y se comparte (coherente con ADR-0003).
- Un 4xx no transitorio de Notion (token/permiso/esquema/versión) devolvía 500; ahora se mapea a
  **502 controlado** sin volcar el cuerpo (M1, A10).
- El default de `NOTION_DATA_SOURCE_ID` era un ID de tenant fijado en el código; ahora es requerido
  por entorno y la app **falla al arrancar** si falta (fail-fast, sin ese ID en el repo) — B2.
- El scoring lanzaba `ZeroDivisionError` (500) ante un conjunto de competencias incompleto; ahora
  valida que estén las 16 y lanza un error de dominio claro antes de promediar — B3.
- La validación de existencia del evaluado era *fail-open*: sin `NOTION_FICHAS_DATA_SOURCE_ID` se
  omitía en silencio. En producción ahora es obligatorio y la app **falla al arrancar** si falta — M1.
- Doc: `/health` se documentaba como "readiness" pero es *liveness* (no comprueba dependencias);
  corregido en README y contrato de API — B2.

### Añadido
- Reintento con backoff exponencial (honra `Retry-After`) e idempotencia de creación en el
  adaptador Notion: ante un fallo transitorio re-verifica por (evaluado, fecha) antes de
  reintentar, para no duplicar — T6/T7, A08/A10.
- Lock por `(evaluado, fecha)` en el caso de uso que cierra la carrera TOCTOU entre la
  verificación de existencia y el guardado (`application/concurrency.py`) — A08.
- Parámetros de reintento configurables: `NOTION_MAX_REINTENTOS`, `NOTION_BACKOFF_BASE_S`,
  `NOTION_BACKOFF_MAX_S`.
- Tests: adaptador Notion (reintento/idempotencia/lectura), concurrencia TOCTOU y verificación JWT.
- Tests de auth a nivel HTTP (401/403/RBAC con auth activada) y de escenarios de abuso del PRD
  (payloads inválidos, inyección tratada como contenido literal, Notion→502, logs sin PII).
- Validación de existencia del evaluado contra la BD 'Fichas' (solo lectura) → 422 si no existe;
  `NOTION_FICHAS_DATA_SOURCE_ID` (vacío = sin validación) — ADR-0007, esc. #5.
- ADR-0007: integridad referencial del evaluado y modelo de acceso **por rol** (sin alcance por
  evaluado); se retira el escenario #3 del PRD y se sustituye por esa política — esc. #3.
- `NOTION_ESTADO_DONE` configurable (opción de la propiedad 'Estado') y contrato de esquema de
  Notion documentado en ADR-0002 (M5). Nota de despliegue de instancia única en el README (M3).
- `GET /v1/resultados`: `response_model` explícito (`ResultadoListItem`) y parámetro `limit`
  (1–100, 50 por defecto) que acota la respuesta (va como `page_size` a Notion) — M3.
- Despliegue con **Docker**: `Dockerfile` multi-stage (instala el lockfile con verificación de
  hashes — A03; runtime sin toolchain, usuario sin privilegios, `--workers 1` fijado por ADR-0007 y
  healthcheck sobre `/health`), `.dockerignore` (excluye `.env`, tests y artefactos) y
  `docker-compose.yml` (secretos por `env_file`, puerto solo en loopback, `read_only`,
  `no-new-privileges`, `cap_drop: ALL` — ADR-0005). Sección de uso en el README.

### Seguridad
- Verificación JWT endurecida: `iss` y `aud` **obligatorios** con JWKS (fail-closed) y `require`
  de `exp`/`iss`/`aud`; rechazo de `alg=none` verificado con test — T1/T3.
- **`APP_ENV=prod`** valida al arrancar y **falla** si la config de auth es insegura (auth
  deshabilitada, sin `JWT_JWKS_URL`, o con `JWT_DEV_SHARED_SECRET`) — M2.
- Tests de la rama de producción **RS256/JWKS** (firma válida, `alg=none`, `aud` incorrecta,
  fail-closed sin iss/aud) — M4.
- **Lockfile con hashes** (`requirements.txt` / `requirements-dev.txt`, `uv pip compile --universal
  --generate-hashes`): el CI instala con verificación de hashes y `pip-audit -r` audita el lock — A03.
- **gitleaks fijado** a una versión concreta y verificado por **sha256 pinneado** en el CI (antes se
  resolvía "latest" dinámicamente): descarga reproducible y evidencia de manipulación — A03, B6.
- `.gitleaks.toml`: mantiene el ruleset por defecto y allowlista solo `apps/mec-aidlc-api/tests/`
  (fixtures con secretos ficticios) para evitar falsos positivos; coherente con `S105/S106` de ruff.
- Se deja de versionar `.coverage` (artefacto de tests) y se amplía `.gitignore` (raíz y del
  subproyecto) para no filtrar artefactos de build/tests — B5.
- `PyJWKClient` usa un **timeout** configurable (`JWT_JWKS_TIMEOUT_S`, 5 s por defecto): el fetch
  de JWKS es bloqueante (threadpool) y un IdP lento no debe degradar el servicio — M2.
- `APP_ENV=prod` exige que `JWT_ALGORITHMS` sean solo **asimétricos** (RS*/ES*/PS*), rechazando
  HS*/`none`: evita la confusión de clave RS/HS con JWKS — B4.
- Verificación JWT con **leeway de reloj** configurable (`JWT_LEEWAY_S`, 30 s) para exp/nbf/iat,
  absorbiendo desfase de reloj entre la API y el IdP — B5.
- El log de auditoría deja de incluir el `estadio` (resultado de evaluación): registra solo quién
  (`sub`) registró para quién (`evaluado`) y cuándo — A09, B3.
- Gate de cobertura ampliado de solo-dominio a **todo el paquete** (adapters/api/application),
  ≥ 90 % (96 % actual; dominio 100 %) — B1.

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
