# Clasificación de Datos

Régimen aplicable: **Ley 1581 de 2012 (Colombia)** y/o **LFPDPPP (México)**. Los resultados
de evaluación son **datos personales** de un titular identificable (relación `Evaluado`) y,
por tratarse de valoración de desempeño, se manejan como **Confidencial/Restringido**:
requieren finalidad declarada, autorización del titular y deber de seguridad.

Niveles: Público < Interno < Confidencial < Restringido.

| Dato | Clasificación | Regulación | Cifrado en reposo | Cifrado en tránsito | Retención |
|---|---|---|---|---|---|
| Identidad del evaluado (relación a ficha) | Restringido | Ley 1581 / LFPDPPP | Sí (en Notion, gestionado por el proveedor) | TLS 1.2+ | Relación laboral + 2 años |
| 16 puntajes de competencia | Confidencial | Ley 1581 / LFPDPPP | Sí (Notion) | TLS 1.2+ | Igual a la evaluación |
| IGV / estadio / promedios | Confidencial | Ley 1581 / LFPDPPP | Sí (Notion) | TLS 1.2+ | Igual a la evaluación |
| Diagnóstico (texto) | Confidencial | Ley 1581 / LFPDPPP | Sí (Notion) | TLS 1.2+ | Igual a la evaluación |
| Fecha del test | Interno | — | Sí (Notion) | TLS 1.2+ | Igual a la evaluación |
| Token de integración Notion | Restringido (secreto) | — | Sí (gestor de secretos, nunca en código) | TLS 1.2+ | Rotación cada 7 días |
| Credenciales del cliente Auth0 (M2M) | Restringido (secreto) | — | Sí (gestor de secretos) | TLS 1.2+ | Rotación cada 7 días |
| Claves de verificación JWT (JWKS Auth0, RS256) | Interno (clave pública) | — | No aplica (clave pública) | TLS 1.2+ | Rotadas por Auth0; el API cachea el JWKS |
| Identidad del evaluador (sub del JWT) | Confidencial | Ley 1581 / LFPDPPP | — | TLS 1.2+ | Logs de auditoría: 1 año |

## Deberes derivados (Ley 1581 / LFPDPPP)
- **Responsable del tratamiento:** Líder de RRHH / People (garante del cumplimiento).
- **Finalidad y autorización:** la finalidad (evaluar la transición de competencias MEC-AIDLC)
  y la autorización del titular se recogen mediante **aviso de privacidad aceptado en el
  onboarding** (autorización general válida para las evaluaciones sucesivas), antes de almacenar
  resultados.
- **Retención:** resultados de evaluación durante la **relación laboral + 2 años** (cubre la
  prescripción de reclamaciones); **logs de auditoría 1 año**. Al vencer, se eliminan/anonimizan.
- **Acceso restringido:** solo evaluadores autorizados (rol) leen/escriben resultados (A01).
- **Trazabilidad:** log de auditoría de quién registró/consultó qué (A09), sin volcar datos
  sensibles en claro en los logs.
- **Minimización:** la API no almacena copia local de resultados; delega en Notion.
