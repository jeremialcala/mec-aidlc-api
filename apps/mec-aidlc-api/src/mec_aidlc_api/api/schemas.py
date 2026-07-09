"""Esquemas de entrada/salida (contrato de API). Validación estricta contra A05.

`extra="forbid"` rechaza campos no esperados; cada competencia es un entero acotado a
[1, 4] (grado Alles A=4, B=3, C=2, D=1).
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from ..domain.scoring import ESCALA_MAX, ESCALA_MIN

_Competencia = Field(..., ge=ESCALA_MIN, le=ESCALA_MAX)


class Competencias(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conocimientos_tecnicos: int = _Competencia
    pensamiento_analitico: int = _Competencia
    pensamiento_conceptual: int = _Competencia
    toma_de_decisiones: int = _Competencia
    orientacion_a_resultados: int = _Competencia
    productividad: int = _Competencia
    planificacion_y_organizacion: int = _Competencia
    gestion_y_logro_de_objetivos: int = _Competencia
    trabajo_en_equipo: int = _Competencia
    colaboracion: int = _Competencia
    comunicacion_eficaz: int = _Competencia
    influencia_y_negociacion: int = _Competencia
    adaptabilidad_a_los_cambios: int = _Competencia
    iniciativa_y_autonomia: int = _Competencia
    desarrollo_y_autodesarrollo: int = _Competencia
    etica_en_el_uso_de_ia: int = _Competencia


class RegistrarResultadoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluado_id: str = Field(..., min_length=1, description="Page ID de la ficha del evaluado")
    fecha_del_test: date
    titulo: str = Field(..., min_length=1, max_length=200)
    competencias: Competencias


class PromediosResponse(BaseModel):
    d1: float
    d2: float
    d3: float
    d4: float


class ResultadoResponse(BaseModel):
    notion_page_url: str
    promedios: PromediosResponse
    igv: float  # escala 1–4
    igv_pct: float  # IGV normalizado a 0–100
    estadio: str
    patron_diagnostico: str


class ResultadoListItem(BaseModel):
    """Proyección liviana de un resultado listado (contrato de salida explícito)."""

    id: str | None = None
    url: str | None = None
