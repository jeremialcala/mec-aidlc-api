# ADR-0003: Autenticación OAuth2 + JWT con control de acceso por rol

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 02-design
- **Controles OWASP afectados:** A01 (access control), A07 (authN)

## Contexto
La API corre en un servidor interno consumido por varios usuarios del equipo (evaluadores).
Los datos son personales de desempeño, así que cada operación debe atribuirse a un usuario
autenticado y autorizado por rol (evaluador puede escribir; consultas restringidas).

## Decisión
Proteger la API con **OAuth2 (bearer) + JWT** emitidos por **Auth0** (IdP confirmado).
La API **valida** tokens (no los emite): firma **RS256** contra el **JWKS** del tenant
(`https://<tenant>.auth0.com/.well-known/jwks.json`) y comprueba `iss` (dominio del tenant,
con barra final), `aud` (API identifier de Auth0) y `exp`. **Vigencia del token: 60 minutos**
(configurada en la API de Auth0). Autorización por rol (`evaluador`, `lector`) leídos de un
claim con namespace añadido por una **Action** de Auth0 (p. ej. `https://mec-aidlc/roles`), o
del claim `permissions` si se habilita RBAC. RBAC **deny-by-default** en la API.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. OAuth2 + JWT | Estándar, atribución por usuario, RBAC, sin sesión en servidor | Requiere IdP y gestión de claves | Bajo si se valida firma+claims |
| B. API key estática | Simple | Sin atribución por persona, difícil de rotar/revocar | Alto (A07): una clave = todos |
| C. Sin auth (solo local) | Nula fricción | Inaceptable para datos personales | Crítico |

## Consecuencias
- Positivas: atribución y auditoría por usuario (A09); ventana de exposición acotada a 60 min
  por la vigencia del token; Auth0 gestiona y rota las claves de firma (el API cachea el JWKS).
- Negativas / deuda asumida: dependencia del tenant Auth0 y de la disponibilidad de su JWKS;
  los roles requieren una Action de Auth0 que añada el claim con namespace (ver `config.py`).
- Impacto en threat model: mitiga T1 (acceso no autorizado) y T5 (repudio); fijar RS256 y
  validar firma/`iss`/`aud`/`exp` mitiga T3 (token forjado, `alg=none`). Rotación de secretos
  bajo nuestro control (token Notion, credenciales Auth0) cada 7 días — ver ADR-0005.
