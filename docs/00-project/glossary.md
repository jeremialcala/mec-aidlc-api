# Glosario / Lenguaje Ubicuo (DDD)

| Término | Definición | Contexto acotado (Bounded Context) |
|---|---|---|
| Evaluación (Resultado del test) | Una aplicación del instrumento MEC-AIDLC a un evaluado en una fecha, con 16 puntajes de competencia. Entidad raíz del agregado. | Evaluación |
| Evaluado | Persona (contribuidor individual) a la que se aplica la evaluación. Referenciada por relación a la BD "Equipo de Desarrollo — Fichas". | Evaluación (referencia externa a Personas) |
| Evaluador | Usuario autenticado que registra el resultado. | Acceso / Identidad |
| Competencia | Cada uno de los 16 ítems evaluados, con nombre tomado del *Diccionario de Alles*. | Evaluación |
| Dominio (D1–D4) | Agrupación de 4 competencias: D1 Técnico-Cognitivo, D2 Resultados y Objetivos, D3 Colaboración e Interacción, D4 Adaptabilidad y Aprendizaje. | Evaluación |
| Promedio de dominio | Media de las 4 competencias de un dominio (lo calcula la fórmula de Notion; la API lo replica para su respuesta). | Evaluación / Scoring |
| IGV (Índice de Generación de Valor) | Índice ponderado 0.20·D̄1 + 0.30·D̄2 + 0.30·D̄3 + 0.20·D̄4, en escala 1–4. Se normaliza a % con `(IGV−1)/3×100`. | Evaluación / Scoring |
| Estadio | Clasificación de madurez: Contribuidor Individual → Team Player → Generador de Valor, según **regla de transición por umbrales de dominio** (no promedio simple). | Evaluación / Scoring |
| Patrón diagnóstico | Interpretación cualitativa del perfil (p. ej. "experto aislado", "buen compañero sin foco", "orquestador sin criterio técnico"). Se persiste en `Diagnóstico`. | Evaluación / Scoring |
| Grado Alles (A–D) | Nivel de desarrollo de una competencia según Martha Alles, codificado como entero: **A=4** (referente), **B=3** (sólido/autónomo), **C=2** (funcional con apoyo), **D=1** (mínimo desarrollado). | Evaluación |
| Regla de transición | Condición basada en umbrales por dominio que determina el estadio; prevalece sobre el promedio para evitar que un dominio alto enmascare un déficit crítico. | Scoring |

> Fuente teórica del vocabulario de competencias: Martha A. Alles, *Diccionario de
> Competencias. La Trilogía, Tomo I* (Granica, 2009).
