# C4 — Diagrama de Contexto

```mermaid
C4Context
  title Contexto del sistema — MEC-AIDLC API
  Person(evaluador, "Evaluador", "Líder técnico / RRHH que registra resultados (rol: evaluador)")
  Person(lector, "Lector", "Consulta resultados (rol: lector)")
  System_Boundary(interno, "Servidor interno del equipo") {
    System(api, "MEC-AIDLC API", "FastAPI: calcula IGV/estadio/diagnóstico y persiste resultados")
  }
  System_Ext(cliente, "Herramienta HTML MEC-AIDLC", "Cliente que envía los 16 puntajes")
  System_Ext(idp, "Proveedor de identidad (IdP)", "Emite JWT OAuth2")
  System_Ext(notion, "Notion — BD Resultados Test MEC-AIDLC", "Sistema de registro; deriva IGV/estadio por fórmula")

  Rel(evaluador, cliente, "Usa")
  Rel(cliente, api, "POST /v1/resultados (JWT)", "HTTPS")
  Rel(lector, api, "GET /v1/resultados (JWT)", "HTTPS")
  Rel(api, idp, "Valida firma/claims del JWT (JWKS)", "HTTPS")
  Rel(api, notion, "Crea/consulta páginas de resultado", "HTTPS + token")
```

> **Trust boundary:** la línea del "Servidor interno del equipo". Todo lo que cruza esa
> frontera (cliente, IdP, Notion) es no confiable y exige validación / autenticación.
