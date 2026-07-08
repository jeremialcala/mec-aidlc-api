"""Test de la carrera TOCTOU de idempotencia en el caso de uso (A08)."""
import asyncio

from mec_aidlc_api.application.concurrency import KeyedLocks
from mec_aidlc_api.application.services import (
    RegistrarResultado,
    ResultadoDuplicadoError,
)
from mec_aidlc_api.domain.models import COMPETENCIA_A_DOMINIO, Evaluacion


class _RepoConcurrente:
    """Fake cuyo existe() refleja lo guardado; cede el control para forzar el interleaving."""

    def __init__(self):
        self.guardados: list[tuple[str, str]] = []

    async def existe(self, evaluado_id, fecha):
        await asyncio.sleep(0)
        return (evaluado_id, fecha) in self.guardados

    async def guardar(self, evaluacion, resultado):
        await asyncio.sleep(0)
        self.guardados.append((evaluacion.evaluado_id, evaluacion.fecha_del_test))
        return "https://notion.so/p"

    async def listar_por_evaluado(self, evaluado_id):
        return []


def _ev():
    return Evaluacion(
        evaluado_id="e1",
        fecha_del_test="2026-07-08",
        titulo="Q3",
        competencias={k: 3 for k in COMPETENCIA_A_DOMINIO},
    )


async def test_envios_concurrentes_misma_clave_no_duplican():
    repo = _RepoConcurrente()
    caso = RegistrarResultado(repo, KeyedLocks())
    resultados = await asyncio.gather(
        caso.ejecutar(_ev()), caso.ejecutar(_ev()), return_exceptions=True
    )
    exitos = [r for r in resultados if not isinstance(r, Exception)]
    duplicados = [r for r in resultados if isinstance(r, ResultadoDuplicadoError)]
    assert len(exitos) == 1
    assert len(duplicados) == 1
    assert len(repo.guardados) == 1  # el lock evitó el duplicado (sin lock serían 2)
