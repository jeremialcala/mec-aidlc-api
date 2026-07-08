"""Rutas de la API MEC-AIDLC."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..adapters.auth import Principal
from ..adapters.notion_repository import NotionUnavailableError
from ..application.ports import ResultRepository
from ..application.services import (
    ListarResultadosPorEvaluado,
    RegistrarResultado,
    ResultadoDuplicadoError,
)
from ..domain.models import Evaluacion
from .deps import get_repository, requiere_rol
from .schemas import PromediosResponse, RegistrarResultadoRequest, ResultadoResponse

logger = logging.getLogger("mec_aidlc_api")

router = APIRouter()


@router.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/v1/resultados",
    response_model=ResultadoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["resultados"],
)
async def registrar_resultado(
    body: RegistrarResultadoRequest,
    principal: Annotated[Principal, Depends(requiere_rol("evaluador"))],
    repo: Annotated[ResultRepository, Depends(get_repository)],
) -> ResultadoResponse:
    evaluacion = Evaluacion(
        evaluado_id=body.evaluado_id,
        fecha_del_test=body.fecha_del_test.isoformat(),
        titulo=body.titulo,
        competencias=body.competencias.model_dump(),
    )
    caso = RegistrarResultado(repo)
    try:
        url, resultado = await caso.ejecutar(evaluacion)
    except ResultadoDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NotionUnavailableError:
        # No filtrar detalles internos (A10).
        logger.warning("Notion no disponible al registrar resultado")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servicio de persistencia no disponible. Reintenta más tarde.",
        )
    # Auditoría sin datos sensibles (A09).
    logger.info(
        "resultado_registrado sub=%s evaluado=%s estadio=%s",
        principal.sub,
        evaluacion.evaluado_id,
        resultado.estadio.value,
    )
    p = resultado.promedios
    return ResultadoResponse(
        notion_page_url=url,
        promedios=PromediosResponse(d1=p.d1, d2=p.d2, d3=p.d3, d4=p.d4),
        igv=resultado.igv,
        igv_pct=resultado.igv_pct,
        estadio=resultado.estadio.value,
        patron_diagnostico=resultado.patron_diagnostico,
    )


@router.get("/v1/resultados", tags=["resultados"])
async def listar_resultados(
    principal: Annotated[Principal, Depends(requiere_rol("evaluador", "lector"))],
    repo: Annotated[ResultRepository, Depends(get_repository)],
    evaluado_id: Annotated[str, Query(min_length=1)],
) -> list[dict]:
    caso = ListarResultadosPorEvaluado(repo)
    try:
        return await caso.ejecutar(evaluado_id)
    except NotionUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servicio de persistencia no disponible.",
        )
