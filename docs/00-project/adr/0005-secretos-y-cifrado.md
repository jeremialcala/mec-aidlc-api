# ADR-0005: Gestión de secretos y cifrado

- **Estado:** accepted
- **Fecha:** 2026-07-08
- **Decisores:** Jeremi
- **Fase AI-DLC:** 02-design
- **Controles OWASP afectados:** A02 (misconfig), A04 (crypto), A03 (supply chain)

## Contexto
La API maneja como secretos: el **token de integración de Notion** (acceso total a la BD de
resultados) y, en su caso, las **credenciales del cliente Auth0** (M2M). Las **claves de
verificación JWT son públicas** (JWKS de Auth0, RS256) — no son secreto y las rota Auth0. El
secreto compartido HS256 existe solo para desarrollo local. Un secreto filtrado compromete
todos los datos personales.

## Decisión
- Cargar secretos solo desde **variables de entorno / gestor de secretos**, nunca en el repo
  (validado con `pydantic-settings`; `.env` en `.gitignore`, `.env.example` sin valores reales).
- **TLS 1.2+** obligatorio para tráfico entrante y hacia la API de Notion.
- Escaneo de secretos y de dependencias (SCA + lockfile) en CI (Gate 2/4).
- **Rotación cada 7 días** de los secretos bajo nuestro control: token de integración Notion
  y credenciales del cliente Auth0 (M2M). Las claves de firma JWT las rota Auth0; el API cachea
  el JWKS y lo revalida, por lo que absorbe la rotación sin cambios de configuración.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| A. Env/secrets manager | Estándar, rotable, fuera del código | Requiere infra de secretos | Bajo |
| B. Secretos en archivo de config versionado | Simple | Filtración garantizada en el repo | Crítico (A02/A04) |

## Consecuencias
- Positivas: sin secretos en código; superficie de fuga reducida.
- Negativas / deuda asumida: dependencia de un gestor de secretos en el servidor interno.
- Impacto en threat model: mitiga T2 (token Notion) y protege la verificación de T1.
