"""Casos de uso de la aplicación."""
from __future__ import annotations

from ..domain import scoring
from ..domain.models import Evaluacion, ResultadoEvaluacion
from .concurrency import KeyedLocks
from .ports import ResultRepository


class ResultadoDuplicadoError(Exception):
    """Ya existe un resultado para (evaluado, fecha) — viola idempotencia (A08)."""


class EvaluadoInexistenteError(Exception):
    """El evaluado no existe en la BD de fichas — evita páginas huérfanas (esc. #5, A05)."""


class RegistrarResultado:
    """Calcula el scoring y persiste una evaluación."""

    def __init__(self, repo: ResultRepository, locks: KeyedLocks) -> None:
        self._repo = repo
        self._locks = locks

    async def ejecutar(self, evaluacion: Evaluacion) -> tuple[str, ResultadoEvaluacion]:
        # Serializa por (evaluado, fecha) para cerrar la carrera TOCTOU entre existe() y guardar()
        # en el proceso; con la creación idempotente del adaptador, evita duplicados (A08).
        clave = f"{evaluacion.evaluado_id}\x00{evaluacion.fecha_del_test}"
        async with self._locks.get(clave):
            if not await self._repo.evaluado_existe(evaluacion.evaluado_id):
                raise EvaluadoInexistenteError(
                    "El evaluado no existe en la base de fichas."
                )
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
