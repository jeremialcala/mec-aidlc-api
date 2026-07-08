"""Núcleo de dominio MEC-AIDLC: entidades y value objects.

Sin dependencias de FastAPI ni de Notion (Clean Architecture — ADR-0004).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Dominio(StrEnum):
    """Los cuatro dominios del marco MEC-AIDLC."""

    D1_TECNICO_COGNITIVO = "D1"
    D2_RESULTADOS_OBJETIVOS = "D2"
    D3_COLABORACION_INTERACCION = "D3"
    D4_ADAPTABILIDAD_APRENDIZAJE = "D4"


# Mapa competencia (clave interna snake_case) -> dominio.
# El orden y agrupación (4x4=16) reflejan el marco MEC-AIDLC.
COMPETENCIA_A_DOMINIO: dict[str, Dominio] = {
    # D1 — Técnico-Cognitivo
    "conocimientos_tecnicos": Dominio.D1_TECNICO_COGNITIVO,
    "pensamiento_analitico": Dominio.D1_TECNICO_COGNITIVO,
    "pensamiento_conceptual": Dominio.D1_TECNICO_COGNITIVO,
    "toma_de_decisiones": Dominio.D1_TECNICO_COGNITIVO,
    # D2 — Resultados y Objetivos
    "orientacion_a_resultados": Dominio.D2_RESULTADOS_OBJETIVOS,
    "productividad": Dominio.D2_RESULTADOS_OBJETIVOS,
    "planificacion_y_organizacion": Dominio.D2_RESULTADOS_OBJETIVOS,
    "gestion_y_logro_de_objetivos": Dominio.D2_RESULTADOS_OBJETIVOS,
    # D3 — Colaboración e Interacción
    "trabajo_en_equipo": Dominio.D3_COLABORACION_INTERACCION,
    "colaboracion": Dominio.D3_COLABORACION_INTERACCION,
    "comunicacion_eficaz": Dominio.D3_COLABORACION_INTERACCION,
    "influencia_y_negociacion": Dominio.D3_COLABORACION_INTERACCION,
    # D4 — Adaptabilidad y Aprendizaje
    "adaptabilidad_a_los_cambios": Dominio.D4_ADAPTABILIDAD_APRENDIZAJE,
    "iniciativa_y_autonomia": Dominio.D4_ADAPTABILIDAD_APRENDIZAJE,
    "desarrollo_y_autodesarrollo": Dominio.D4_ADAPTABILIDAD_APRENDIZAJE,
    "etica_en_el_uso_de_ia": Dominio.D4_ADAPTABILIDAD_APRENDIZAJE,
}

# Nombre interno -> nombre exacto de la propiedad en Notion (para el adaptador).
COMPETENCIA_A_NOTION: dict[str, str] = {
    "conocimientos_tecnicos": "Conocimientos técnicos",
    "pensamiento_analitico": "Pensamiento analítico",
    "pensamiento_conceptual": "Pensamiento conceptual",
    "toma_de_decisiones": "Toma de decisiones",
    "orientacion_a_resultados": "Orientación a resultados",
    "productividad": "Productividad",
    "planificacion_y_organizacion": "Planificación y organización",
    "gestion_y_logro_de_objetivos": "Gestión y logro de objetivos",
    "trabajo_en_equipo": "Trabajo en equipo",
    "colaboracion": "Colaboración",
    "comunicacion_eficaz": "Comunicación eficaz",
    "influencia_y_negociacion": "Influencia y negociación",
    "adaptabilidad_a_los_cambios": "Adaptabilidad a los cambios",
    "iniciativa_y_autonomia": "Iniciativa y autonomía",
    "desarrollo_y_autodesarrollo": "Desarrollo y autodesarrollo",
    "etica_en_el_uso_de_ia": "Ética en el uso de IA",
}


class Estadio(StrEnum):
    """Estadios de madurez del marco MEC-AIDLC."""

    CONTRIBUIDOR_INDIVIDUAL = "Contribuidor Individual"
    TEAM_PLAYER = "Team Player"
    GENERADOR_DE_VALOR = "Generador de Valor"


@dataclass(frozen=True)
class ResultadoDominio:
    """Promedios por dominio (1–4)."""

    d1: float
    d2: float
    d3: float
    d4: float


@dataclass(frozen=True)
class ResultadoEvaluacion:
    """Resultado calculado de una evaluación (value object de salida del scoring)."""

    promedios: ResultadoDominio
    igv: float  # escala 1–4
    igv_pct: float  # IGV normalizado a 0–100 (ADR-0006)
    estadio: Estadio
    patron_diagnostico: str


@dataclass(frozen=True)
class Evaluacion:
    """Agregado raíz: una aplicación del instrumento a un evaluado."""

    evaluado_id: str
    fecha_del_test: str  # ISO-8601 (YYYY-MM-DD)
    titulo: str
    competencias: dict[str, int]  # 16 claves de COMPETENCIA_A_DOMINIO, enteros 1–4
