"""Scoring MEC-AIDLC: promedios de dominio, IGV, estadio y patrón diagnóstico.

Fuente de verdad reproducible (probada sin red). Escala y umbrales confirmados en ADR-0006:
cada ítem es un entero 1–4 (grados Alles A=4, B=3, C=2, D=1); los umbrales de la regla de
transición viven en escala 1–4 con pivote 3.0 (grado B). Cámbialos aquí en un único lugar.
"""
from __future__ import annotations

from .models import (
    COMPETENCIA_A_DOMINIO,
    Dominio,
    Estadio,
    ResultadoDominio,
    ResultadoEvaluacion,
)

# --- Escala (ADR-0006, confirmada): grado Alles A=4, B=3, C=2, D=1 ---
ESCALA_MIN = 1
ESCALA_MAX = 4

# Ponderaciones del IGV (confirmadas por el marco MEC-AIDLC).
PESO_IGV: dict[Dominio, float] = {
    Dominio.D1_TECNICO_COGNITIVO: 0.20,
    Dominio.D2_RESULTADOS_OBJETIVOS: 0.30,
    Dominio.D3_COLABORACION_INTERACCION: 0.30,
    Dominio.D4_ADAPTABILIDAD_APRENDIZAJE: 0.20,
}

# --- Umbrales de la regla de transición (ADR-0006, confirmada; escala 1–4, pivote 3.0=B) ---
# Regla por umbrales de dominio, NO por promedio simple: un dominio alto no debe
# enmascarar un déficit crítico en otro.
UMBRAL_GV_IGV = 3.0
UMBRAL_GV_D2 = 3.0
UMBRAL_GV_D3 = 3.0
UMBRAL_GV_D1 = 2.4
UMBRAL_GV_D4 = 2.4

UMBRAL_TP_D3 = 2.4
UMBRAL_TP_D1 = 2.0

# Umbrales para detección de patrones diagnósticos (B=3.0 alto, C=2.0 bajo).
ALTO = 3.0
BAJO = 2.0


def _validar_competencias(competencias: dict[str, int]) -> None:
    """Exige exactamente las 16 competencias del marco (defensa del dominio).

    La API ya valida el esquema (Pydantic `extra=forbid`, 16 campos), pero el dominio no debe
    asumirlo: un dict parcial dejaría a `_promedio` dividiendo por cero. Falla claro y temprano.
    """
    esperadas = set(COMPETENCIA_A_DOMINIO)
    recibidas = set(competencias)
    if recibidas != esperadas:
        faltan = sorted(esperadas - recibidas)
        sobran = sorted(recibidas - esperadas)
        raise ValueError(f"Competencias inválidas (faltan={faltan}, sobran={sobran}).")


def _promedio(competencias: dict[str, int], dominio: Dominio) -> float:
    valores = [
        v for k, v in competencias.items() if COMPETENCIA_A_DOMINIO[k] == dominio
    ]
    return round(sum(valores) / len(valores), 2)


def calcular_promedios(competencias: dict[str, int]) -> ResultadoDominio:
    return ResultadoDominio(
        d1=_promedio(competencias, Dominio.D1_TECNICO_COGNITIVO),
        d2=_promedio(competencias, Dominio.D2_RESULTADOS_OBJETIVOS),
        d3=_promedio(competencias, Dominio.D3_COLABORACION_INTERACCION),
        d4=_promedio(competencias, Dominio.D4_ADAPTABILIDAD_APRENDIZAJE),
    )


def calcular_igv(p: ResultadoDominio) -> float:
    # El IGV se deriva de los promedios ya redondeados a 2 decimales (los mismos que se muestran
    # y persisten), no de los ítems crudos: fuente única y reproducible. El redondeo doble es
    # intencional y coherente con los valores almacenados (no un artefacto).
    igv = (
        PESO_IGV[Dominio.D1_TECNICO_COGNITIVO] * p.d1
        + PESO_IGV[Dominio.D2_RESULTADOS_OBJETIVOS] * p.d2
        + PESO_IGV[Dominio.D3_COLABORACION_INTERACCION] * p.d3
        + PESO_IGV[Dominio.D4_ADAPTABILIDAD_APRENDIZAJE] * p.d4
    )
    return round(igv, 2)


def normalizar_igv_pct(igv: float) -> float:
    """Normaliza el IGV (escala 1–4) a porcentaje lineal 0–100 (ADR-0006).

    %IGV = (IGV - 1) / 3 * 100 → 1.0 = 0 %, 2.5 = 50 %, 4.0 = 100 %.
    """
    return round((igv - ESCALA_MIN) / (ESCALA_MAX - ESCALA_MIN) * 100, 2)


def clasificar_estadio(p: ResultadoDominio, igv: float) -> Estadio:
    """Regla de transición por umbrales de dominio (ADR-0006)."""
    es_generador = (
        igv >= UMBRAL_GV_IGV
        and p.d2 >= UMBRAL_GV_D2
        and p.d3 >= UMBRAL_GV_D3
        and p.d1 >= UMBRAL_GV_D1
        and p.d4 >= UMBRAL_GV_D4
    )
    if es_generador:
        return Estadio.GENERADOR_DE_VALOR

    es_team_player = p.d3 >= UMBRAL_TP_D3 and p.d1 >= UMBRAL_TP_D1
    if es_team_player:
        return Estadio.TEAM_PLAYER

    return Estadio.CONTRIBUIDOR_INDIVIDUAL


def diagnosticar_patron(p: ResultadoDominio, estadio: Estadio) -> str:
    """Patrón diagnóstico cualitativo del perfil (se persiste en `Diagnóstico`)."""
    if estadio == Estadio.GENERADOR_DE_VALOR:
        return "Generador de valor: resultados y colaboración consolidados sobre base técnica."

    # Patrones de perfil desequilibrado (prioridad: el desbalance más crítico).
    if p.d1 >= ALTO and p.d3 <= BAJO:
        return "Experto aislado: fuerte técnicamente, débil en colaboración e interacción."
    if p.d3 >= ALTO and p.d2 <= BAJO:
        return "Buen compañero sin foco: colabora bien, pero flojo en resultados y objetivos."
    if p.d3 >= ALTO and p.d1 <= BAJO:
        return "Orquestador sin criterio técnico: coordina, pero le falta profundidad técnica."
    if p.d2 >= ALTO and p.d3 <= BAJO:
        return "Ejecutor individual: entrega resultados, pero poco integrado al equipo."
    if p.d4 <= BAJO:
        return "Rígido: adaptabilidad y aprendizaje por debajo del umbral esperado."

    if estadio == Estadio.TEAM_PLAYER:
        return (
            "Team player en desarrollo: base equilibrada, "
            "sin destacar aún en generación de valor."
        )
    return "Contribuidor individual: aún por consolidar colaboración y/o resultados."


def evaluar(competencias: dict[str, int]) -> ResultadoEvaluacion:
    """Punto de entrada del scoring: de 16 puntajes (1–4) a resultado completo."""
    _validar_competencias(competencias)
    promedios = calcular_promedios(competencias)
    igv = calcular_igv(promedios)
    estadio = clasificar_estadio(promedios, igv)
    patron = diagnosticar_patron(promedios, estadio)
    return ResultadoEvaluacion(
        promedios=promedios,
        igv=igv,
        igv_pct=normalizar_igv_pct(igv),
        estadio=estadio,
        patron_diagnostico=patron,
    )
