# Contratos de API — MEC-AIDLC API

## Endpoints
| Método | Ruta | Auth | Rol | Descripción |
|---|---|---|---|---|
| GET | `/health` | No | — | Liveness/readiness (sin datos sensibles) |
| POST | `/v1/resultados` | JWT | evaluador | Registra un resultado y devuelve el derivado |
| GET | `/v1/resultados` | JWT | evaluador, lector | Lista resultados por `evaluado_id` |

## POST /v1/resultados — request (JSON)
```json
{
  "evaluado_id": "notion-page-uuid-de-la-ficha",
  "fecha_del_test": "2026-07-08",
  "titulo": "Evaluación Q3 — <persona>",
  "competencias": {
    "conocimientos_tecnicos": 3,
    "pensamiento_analitico": 3,
    "pensamiento_conceptual": 2,
    "toma_de_decisiones": 2,
    "orientacion_a_resultados": 3,
    "productividad": 3,
    "planificacion_y_organizacion": 2,
    "gestion_y_logro_de_objetivos": 3,
    "trabajo_en_equipo": 4,
    "colaboracion": 3,
    "comunicacion_eficaz": 3,
    "influencia_y_negociacion": 2,
    "adaptabilidad_a_los_cambios": 3,
    "iniciativa_y_autonomia": 3,
    "desarrollo_y_autodesarrollo": 2,
    "etica_en_el_uso_de_ia": 4
  }
}
```
Validación: cada competencia es un **entero en `[1, 4]`** (grado Alles A=4, B=3, C=2, D=1);
`extra=forbid`; `evaluado_id` y `fecha` obligatorios.

## POST /v1/resultados — response 201 (JSON)
```json
{
  "notion_page_url": "https://www.notion.so/...",
  "promedios": { "d1": 2.5, "d2": 2.75, "d3": 3.0, "d4": 3.0 },
  "igv": 2.83,
  "igv_pct": 61.0,
  "estadio": "Team Player",
  "patron_diagnostico": "Team player en desarrollo: base equilibrada, sin destacar aún en generación de valor."
}
```
`igv` va en escala 1–4; `igv_pct` es su normalización lineal a 0–100 (`(igv−1)/3×100`).

## GET /v1/resultados — query + response 200 (JSON)
Query: `evaluado_id` (requerido) y `limit` (opcional, entero `[1, 100]`, por defecto `50`).
Respuesta: lista acotada de proyecciones livianas (una página de Notion; sin cursor todavía).
```json
[
  { "id": "notion-page-uuid", "url": "https://www.notion.so/..." }
]
```

## Códigos de error
| Código | Caso | OWASP |
|---|---|---|
| 401 | JWT ausente/invalid/expirado | A07 |
| 403 | Rol insuficiente | A01 |
| 422 | Esquema inválido / evaluado inexistente | A05 |
| 409 | Duplicado (idempotencia) | A08 |
| 502/503 | Notion no disponible | A10 |

## Esqueleto OpenAPI
> Se genera automáticamente en `/openapi.json` y `/docs` desde FastAPI + Pydantic.
> El contrato canónico son los esquemas en `apps/mec-aidlc-api/src/mec_aidlc_api/api/schemas.py`.
