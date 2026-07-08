# PRD — Registro de resultados de evaluación MEC-AIDLC

- **Fase AI-DLC:** 01-requirements
- **Estado:** review

## Problema y contexto
La evaluación MEC-AIDLC hoy exporta a CSV manualmente. El equipo necesita registrar los
resultados directamente en la BD Notion "Resultados Test MEC-AIDLC", con IGV, estadio y
diagnóstico consistentes, y con acceso controlado por tratarse de datos personales de desempeño.

## Objetivos / No-objetivos
- **Objetivos:** registrar un resultado (16 competencias + evaluado + fecha), calcular
  dominio/IGV/estadio/patrón, persistir en Notion, consultar resultados por evaluado.
- **No-objetivos:** UI de captura, gestión de personas, edición de fórmulas Notion, analítica.

## Usuarios y escenarios
Actores: **Evaluador** (rol que escribe), **Lector** (rol de solo consulta), **Cliente**
(la herramienta HTML MEC-AIDLC u otro consumidor autenticado), **Notion** (sistema externo).

### Escenarios positivos
1. Un evaluador autenticado envía 16 puntajes + evaluado + fecha → la API calcula IGV/estadio/
   diagnóstico y crea una página en Notion; responde con el resultado derivado y el enlace.
2. Un lector consulta los resultados de un evaluado → recibe la lista con IGV y estadio.

### Escenarios negativos / abuso (requerido por Gate 0)
1. **Sin token o token inválido/expirado** → 401; nada se persiste. (A07)
2. **Lector intenta registrar** → 403 por rol insuficiente. (A01)
3. **Evaluador consulta resultados de un evaluado fuera de su alcance** → 403 / filtrado. (A01)
4. **Payload malicioso:** competencia fuera de rango, tipo inválido, campos extra, valores
   enormes, inyección en `Diagnóstico`/título → 422 por validación de esquema estricta;
   los textos se envían a Notion como contenido, nunca interpolados en fórmulas ni queries. (A05)
5. **Evaluado inexistente en la BD de personas** → 422; no se crea página huérfana.
6. **Notion caído / rate-limit / timeout** → 502/503 controlado con reintento idempotente;
   sin filtrar detalles internos en el error. (A10)
7. **Token de Notion filtrado en logs** → prohibido: los secretos y los puntajes no se
   registran en claro en logs. (A09/A04)
8. **Reenvío duplicado** (doble submit del cliente) → idempotencia por clave
   (evaluado + fecha del test) para no duplicar páginas. (A08)
9. **Escalado de privilegios vía claim manipulado** → firma JWT verificada; claims de rol no confiables sin firma válida. (A01/A07)

## Requisitos funcionales
- RF1: `POST /v1/resultados` registra un resultado y devuelve el derivado (IGV, estadio, patrón).
- RF2: `GET /v1/resultados?evaluado_id=...` lista resultados de un evaluado.
- RF3: El scoring (dominio/IGV/estadio/patrón) se calcula en el dominio y es reproducible.
- RF4: Solo se escriben campos editables de Notion; los campos fórmula no se tocan.
- RF5: `GET /health` sin autenticación para readiness/liveness (sin datos sensibles).

## Requisitos de seguridad (mapeados a OWASP ASVS)
| Req | ASVS | Nivel | OWASP Top 10 |
|---|---|---|---|
| Validar firma, exp, iss y aud del JWT | V3.5 / V7 | L2 | A07 |
| RBAC por rol para escritura vs lectura | V4.1 | L2 | A01 |
| Validación estricta de esquema de entrada (rangos, tipos, campos extra prohibidos) | V5.1 | L2 | A05 |
| TLS 1.2+ en tránsito (entrada y hacia Notion) | V9.1 | L2 | A04 |
| Secretos solo en env/secrets manager, nunca en repo | V6.4 / V14.3 | L2 | A02/A04 |
| Logging de auditoría (quién/qué/cuándo) sin datos sensibles en claro | V7.1 | L2 | A09 |
| Manejo de errores sin fuga de stack/detalles internos | V7.4 | L2 | A10 |
| Idempotencia y verificación de integridad al persistir | V5.2 | L2 | A08 |
| SCA + lockfile de dependencias (incluye SDK Notion) | V14.2 | L2 | A03 |

## Métricas de éxito
- 100 % de escrituras atribuidas a un usuario autenticado.
- 0 duplicados por reenvío (idempotencia efectiva).
- Cobertura de scoring ≥ 90 %; validación de esquema con tests de payloads de abuso.

## Dependencias y riesgos
- Dependencia: API de Notion y esquema/fórmulas existentes (ADR-0002).
- Dependencia: escala 1–4 y umbrales confirmados (ADR-0006) deben seguir en sincronía con
  las fórmulas de Notion y la herramienta HTML si estas cambian.
- Riesgo: disponibilidad de Notion (A10) → SPOF de persistencia.
