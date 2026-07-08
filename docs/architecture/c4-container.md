# C4 — Diagrama de Contenedores

```mermaid
C4Container
  title Contenedores — MEC-AIDLC API
  Person(evaluador, "Evaluador", "rol: evaluador")
  System_Ext(notion, "Notion API", "BD Resultados + fórmulas IGV/Estadio")
  System_Ext(idp, "IdP / JWKS", "Claves de verificación JWT")

  System_Boundary(api, "MEC-AIDLC API (FastAPI)") {
    Container(web, "Capa API", "FastAPI / Uvicorn", "Routers, esquemas Pydantic, RBAC, manejo de errores")
    Container(app, "Aplicación", "Python", "Casos de uso + puertos (ResultRepository)")
    Container(dom, "Dominio", "Python puro", "Scoring: IGV, estadio, patrón diagnóstico")
    Container(adp, "Adaptadores", "Python + httpx", "NotionResultRepository, verificación JWT")
  }

  Rel(evaluador, web, "HTTPS + Bearer JWT")
  Rel(web, app, "invoca casos de uso")
  Rel(app, dom, "calcula scoring")
  Rel(app, adp, "usa puerto ResultRepository")
  Rel(adp, notion, "crea/consulta páginas", "HTTPS + token (secrets manager)")
  Rel(web, idp, "descarga JWKS y valida token", "HTTPS")
```

> **Trust boundary** en la capa API: validación de esquema + verificación JWT antes de
> alcanzar la aplicación y el dominio. Los adaptadores son el único punto que habla con
> sistemas externos.
