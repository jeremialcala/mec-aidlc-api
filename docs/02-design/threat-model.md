# Threat Model — MEC-AIDLC API (sistema)

- **Alcance:** sistema completo (API + integraciones IdP y Notion)
- **Fecha / versión:** 2026-07-08 · v0.1
- **Clasificación de datos:** ver `docs/00-project/data-classification.md`

## Diagrama de flujo de datos
Ver `docs/architecture/c4-context.md` y `c4-container.md`. Trust boundary = borde del
servidor interno y borde de la capa API. Cruces no confiables: Cliente→API, API→IdP, API→Notion.

## Análisis STRIDE
| Componente | Spoofing | Tampering | Repudiation | Info Disclosure | DoS | Elevation |
|---|---|---|---|---|---|---|
| Capa API (entrada) | JWT inválido suplanta usuario | Payload alterado | Escritura sin atribución | Mensajes de error con PII | Flood de requests | Rol falsificado |
| Verificación JWT | Token forjado | Claims manipulados | — | Filtrar clave de verificación | JWKS no disponible | `alg=none`/rol elevado |
| Adaptador Notion | Suplantar la API ante Notion | Alterar payload a Notion | — | Token Notion en logs | Rate-limit/caída | Integración con permisos excesivos |
| Notion (externo) | — | Cambio de esquema/fórmula | — | Exposición de la BD | Indisponibilidad | — |
| Logs / auditoría | — | Borrado de rastro | Negar acción | PII/puntajes en claro | — | — |

## Amenazas priorizadas (DREAD)
Escala 1–3 por factor (Damage, Reproducibility, Exploitability, Affected users, Discoverability). Score = suma (máx 15).

| ID | Amenaza | D | R | E | A | D | Score | Control / ADR |
|---|---|---|---|---|---|---|---|---|
| T1 | Acceso no autorizado / suplantación para leer o escribir resultados | 3 | 2 | 2 | 3 | 2 | 12 | OAuth2+JWT, RBAC deny-by-default, validar iss/aud/exp/firma → ADR-0003, A01/A07 |
| T2 | Token de integración Notion comprometido (acceso total a la BD) | 3 | 2 | 2 | 3 | 1 | 11 | Secrets manager, rotación, mínimo privilegio de la integración, no en logs → ADR-0005, A02/A04 |
| T3 | Elevación por token forjado (`alg=none`, clave débil, rol en claim no verificado) | 3 | 2 | 2 | 3 | 1 | 11 | Fijar algoritmos permitidos, verificar firma con JWKS, no confiar en claims sin firma → ADR-0003, A07/A01 |
| T4 | Inyección / payload malicioso en puntajes o texto | 2 | 3 | 2 | 2 | 2 | 11 | Pydantic estricto (rangos, tipos, `extra=forbid`), texto como contenido no interpolado → A05 |
| T5 | Fuga de datos personales en errores o logs | 3 | 2 | 1 | 3 | 1 | 10 | Manejo de errores genérico, logs sin PII/puntajes/secretos → A09/A10 |
| T6 | Indisponibilidad/caída de Notion (SPOF de persistencia) | 2 | 3 | 1 | 3 | 2 | 11 | Timeout, reintento con backoff, respuesta 502/503 controlada, idempotencia → ADR-0002, A10 |
| T7 | Duplicación de resultados por reenvío | 1 | 3 | 2 | 2 | 2 | 10 | Clave de idempotencia (evaluado+fecha), verificación previa → A08 |
| T8 | Dependencia de terceros vulnerable (SDK Notion, libs JWT) | 2 | 2 | 1 | 3 | 2 | 10 | SCA + lockfile + actualización → A03 |

## Controles y trazabilidad
Cada amenaza traza a un control OWASP y/o ADR (columna final). Todas las decisiones de control
están confirmadas (Auth0 RS256/JWKS, rotación de secretos cada 7 días, escala/umbrales 1–4);
no quedan controles en `<TODO>`. Ninguna amenaza queda sin control asignado.
