"""Puertos (interfaces) de la capa de aplicación — Clean Architecture (ADR-0004).

Los adaptadores de infraestructura implementan estos protocolos; la aplicación no conoce
Notion ni HTTP.
"""
from __future__ import annotations

from typing import Protocol

from ..domain.models import Evaluacion, ResultadoEvaluacion


class ResultRepository(Protocol):
    """Persistencia de resultados de evaluación."""

    async def existe(self, evaluado_id: str, fecha_del_test: str) -> bool:
        """True si ya existe un resultado para (evaluado, fecha) — idempotencia (A08)."""
        ...

    async def evaluado_existe(self, evaluado_id: str) -> bool:
        """True si el evaluado existe en la BD de fichas (integridad referencial, esc. #5)."""
        ...

    async def guardar(
        self, evaluacion: Evaluacion, resultado: ResultadoEvaluacion
    ) -> str:
        """Persiste el resultado y devuelve la URL de la página creada."""
        ...

    async def listar_por_evaluado(
        self, evaluado_id: str, limit: int = 50
    ) -> list[dict]:
        """Lista resultados de un evaluado (proyección liviana, acotada por `limit`)."""
        ...
