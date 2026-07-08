"""Casos de uso de la aplicación."""
from __future__ import annotations

from ..domain import scoring
from ..domain.models import Evaluacion, ResultadoEvaluacion
from .ports import ResultRepository


class ResultadoDuplicadoError(Exception):
    """Ya existe un resultado para (evaluado, fecha) — viola idempotencia (A08)."""


class RegistrarResultado:
    """Calcula el scoring y persiste una evaluación."""

    def __init__(self, repo: ResultRepository) -> None:
        self._repo = repo

    async def ejecutar(self, evaluacion: Evaluacion) -> tuple[str, ResultadoEvaluacion]:
        if await self._repo.existe(evaluacion.evaluado_id, evaluacion.fecha_del_test):
            raise ResultadoDuplicadoError(
                "Ya existe un resultado para ese evaluado y fecha."
            )
        resultado = scoring.evaluar(evaluacion.competencias)
        url = await self._repo.guardar(evaluacion, resultado)
        return url, resultado


class ListarResultadosPorEvaluado:
    def __init__(self, repo: ResultRepository) -> None:
        self._repo = repo

    async def ejecutar(self, evaluado_id: str) -> list[dict]:
        return await self._repo.listar_por_evaluado(evaluado_id)
