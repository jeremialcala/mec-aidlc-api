# Diseño del Sistema — MEC-AIDLC API

## Estilo arquitectónico
**Clean Architecture / hexagonal** (ADR-0004). Regla de dependencia hacia adentro:

```
api  →  application  →  domain
              ▲
          adapters  (implementan puertos de application)
```

- `domain/` — núcleo puro: entidades (`Evaluacion`), value objects (`PuntajesCompetencia`,
  `ResultadoDominio`) y **scoring** (IGV, estadio, patrón diagnóstico). Sin I/O ni frameworks.
- `application/` — casos de uso (`RegistrarResultado`, `ListarResultadosPorEvaluado`) y
  **puertos** (`ResultRepository`).
- `adapters/` — `NotionResultRepository` (SDK/HTTP de Notion) y verificación JWT.
- `api/` — FastAPI: routers, esquemas Pydantic (validación de entrada/salida), dependencias
  (auth, repositorio).

## Contextos acotados (DDD)
| Bounded Context | Responsabilidad | Entidades núcleo |
|---|---|---|
| Evaluación | Registrar y calcular resultados MEC-AIDLC | Evaluacion, Competencia, ResultadoDominio |
| Scoring | IGV, estadio, patrón diagnóstico (reglas) | ReglaTransicion, PatronDiagnostico |
| Acceso / Identidad | AuthN/Z (JWT + rol) | Usuario (sub), Rol |
| Personas (externo) | Catálogo de evaluados (BD "Fichas") | referencia por `evaluado_id` |

## Vista C4
Ver `docs/architecture/c4-context.md` y `docs/architecture/c4-container.md` (Mermaid).

## Contratos de API
Ver `docs/02-design/api-contract.md` (tabla de endpoints + esqueleto OpenAPI).

## Mapeo a Notion (solo campos editables)
| Concepto de dominio | Propiedad Notion | Tipo | Escribe la API |
|---|---|---|---|
| Título del resultado | `Resultado` | title | Sí |
| Evaluado | `Evaluado` | relation | Sí (page id de la ficha) |
| Fecha del test | `Fecha del test` | date | Sí |
| 16 competencias | (16 propiedades number) | number | Sí |
| Patrón diagnóstico | `Diagnóstico` | text | Sí |
| Estado del registro | `Estado` | status | Sí (p. ej. "Done") |
| Promedio D1–D4, IGV, Estadio | fórmulas | formula | **No** (solo lectura) |

## Patrones de seguridad seleccionados (por amenaza DREAD priorizada)
| Amenaza | Patrón / Control | OWASP |
|---|---|---|
| T1 Acceso no autorizado a resultados | OAuth2+JWT, RBAC, deny-by-default | A01/A07 |
| T2 Token Notion comprometido | Secrets manager, rotación, mínimo privilegio de la integración | A02/A04 |
| T3 Inyección/payload malicioso | Esquema Pydantic estricto, sin interpolar texto en queries | A05 |
| T4 Caída de Notion | Timeout + reintento idempotente + degradación controlada | A10 |
| T5 Repudio de escritura | Log de auditoría firmado por `sub` del JWT | A09 |
| T6 Duplicados/integridad | Clave de idempotencia (evaluado+fecha) | A08 |
