# MEC-AIDLC API

API REST (FastAPI) que registra resultados de la evaluación **MEC-AIDLC** en la base de
datos Notion *Resultados Test MEC-AIDLC*. Calcula promedios por dominio, IGV, estadio y
patrón diagnóstico, y persiste solo los campos editables (Notion deriva IGV/estadio por fórmula).

## Arquitectura (Clean / hexagonal — ADR-0004)
```
api/          FastAPI: rutas, esquemas Pydantic, RBAC, manejo de errores
application/  casos de uso + puertos (ResultRepository)
domain/       scoring puro: IGV, estadio, patrón diagnóstico (probado sin red)
adapters/     NotionResultRepository (httpx) + verificación JWT
```
Regla de dependencia: `api → application → domain`; `adapters` implementa puertos.

## Requisitos
- Python 3.11+
- Un token de integración Notion con acceso a la BD de resultados.
- Un tenant **Auth0** (IdP) que emita JWT RS256 (para prod); tokens de 60 min.

## Instalación
```bash
cd apps/mec-aidlc-api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                 # desarrollo (resuelve deps desde pyproject)
cp .env.example .env                     # rellena NOTION_TOKEN y config JWT
```

Instalación reproducible (igual que el CI), verificando hashes desde el lockfile:
```bash
pip install -r requirements-dev.txt      # versiones exactas + hashes (A03)
pip install -e . --no-deps
```

Regenerar el lockfile tras cambiar dependencias (requiere `uv`):
```bash
uv pip compile --universal --generate-hashes -o requirements.txt pyproject.toml
uv pip compile --universal --generate-hashes --extra dev -o requirements-dev.txt pyproject.toml
```

## Ejecutar
```bash
uvicorn mec_aidlc_api.main:app --reload --app-dir src
# Docs interactivas: http://localhost:8000/docs
```

## Tests
```bash
pytest        # 56 tests: scoring, JWT (verificación + auth HTTP), adaptador Notion, TOCTOU y abuso del PRD (1–9)
```

## Endpoints
| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `/health` | — | Liveness/readiness |
| POST | `/v1/resultados` | evaluador | Registra un resultado y devuelve el derivado |
| GET | `/v1/resultados?evaluado_id=...` | evaluador, lector | Lista resultados de un evaluado |

Contrato completo: `../../docs/02-design/api-contract.md`.

## Seguridad
- OAuth2 + JWT vía **Auth0** (RS256/JWKS, firma/exp/iss/aud; roles por claim con namespace),
  RBAC deny-by-default — ADR-0003.
- Validación estricta de esquema (`extra=forbid`, ítems enteros 1–4) — A05.
- Secretos solo desde entorno; `.env` fuera del repo — ADR-0005.
- Idempotencia por (evaluado + fecha): lock anti-TOCTOU en el caso de uso + creación idempotente — A08.
- Reintento con backoff ante caídas/rate-limit de Notion; errores sin fuga de detalles; logs de
  auditoría sin datos sensibles — A09/A10.

> **Escala y umbrales confirmados (ADR-0006 `accepted`):** ítems enteros 1–4 (grados Alles
> A=4…D=1); regla de transición por umbrales con pivote 3.0=B. Centralizados en `domain/scoring.py`.
