# Project Charter — MEC-AIDLC API

## Visión
Servicio backend que registra de forma segura los resultados de la evaluación de
competencias **MEC-AIDLC** en la base de datos Notion "Resultados Test MEC-AIDLC",
para que el equipo de desarrollo pueda persistir, consultar y analizar la transición
Contribuidor Individual → Team Player → Generador de Valor sin depender de exportaciones
manuales CSV.

## Alcance
- Incluye:
  - Endpoint para registrar un resultado de evaluación (16 competencias, evaluado, fecha).
  - Cálculo de dominio (D1–D4), Índice de Generación de Valor (IGV), estadio y patrón
    diagnóstico en el núcleo de dominio (fuente de verdad reproducible en tests).
  - Persistencia en Notion escribiendo únicamente los campos editables (16 competencias +
    `Evaluado` + `Fecha del test` + `Diagnóstico` + `Estado` + `Resultado`/título);
    `Promedio D1–D4`, `IGV` y `Estadio` los deriva Notion vía fórmula.
  - Consulta de resultados por evaluado.
  - AuthN/Z con OAuth2 + JWT y control de acceso por rol.
- **No incluye (no-scope):**
  - Frontend / recolección de respuestas (lo hace la herramienta HTML MEC-AIDLC existente).
  - Gestión del catálogo de personas evaluadas (vive en la BD "Equipo de Desarrollo — Fichas").
  - Definición/edición de las fórmulas de IGV y estadio dentro de Notion.
  - Analítica avanzada, dashboards o validación psicométrica (Cronbach, etc.).

## Stakeholders
| Rol | Nombre | Responsabilidad |
|---|---|---|
| Product owner / investigador | Jeremi | Define el marco MEC-AIDLC, umbrales y regla de transición |
| Evaluador | Líderes técnicos / RRHH | Ejecutan la evaluación y envían resultados vía cliente |
| Responsable de datos | Líder de RRHH / People | Garantiza cumplimiento Ley 1581 / LFPDPPP |
| Operador | Equipo de plataforma | Despliega y opera la API en el servidor interno |

## Restricciones y supuestos
- Stack fijo: **Python 3.11+ / FastAPI**.
- Persistencia externa vía **API de Notion** (no hay base de datos propia).
- Despliegue en **servidor interno del equipo** (no expuesto a Internet público).
- Regulación: **Ley 1581 (Colombia) / LFPDPPP (México)** — datos personales de titular identificable.
- Supuesto: la BD Notion y sus fórmulas (IGV, Estadio, Promedios) ya existen y no cambian de esquema.
- Escala confirmada: entero **1–4** por competencia (grados Alles A=4…D=1), ver ADR-0006.
- Umbrales de la regla de transición confirmados (pivote 3.0=B), en `domain/scoring.py`.

## Métricas de éxito del proyecto
- Un resultado enviado se refleja en Notion con IGV y estadio correctos en < 5 s.
- 0 exportaciones CSV manuales tras la adopción.
- Cobertura de tests del núcleo de dominio (scoring) ≥ 90 %.
- 0 resultados persistidos sin evaluado asociado ni autorización válida.

## Riesgos de alto nivel
- **Fuga de datos personales de desempeño** (impacto alto, regulado). → threat model T1.
- **Token de Notion comprometido** → escritura/lectura no autorizada de toda la BD. → T2.
- **Divergencia de escala/umbrales** entre la herramienta HTML y esta API → resultados inconsistentes.
- **Dependencia dura de la disponibilidad de la API de Notion** (SPOF de persistencia).
