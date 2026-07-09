"""Rutas de la API MEC-AIDLC."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..adapters.auth import Principal
from ..adapters.notion_repository import NotionUnavailableError
from ..application.concurrency import KeyedLocks
from ..application.ports import ResultRepository
from ..application.services import (
    EvaluadoInexistenteError,
    ListarResultadosPorEvaluado,
    RegistrarResultado,
    ResultadoDuplicadoError,
)
from ..domain.models import Evaluacion
from .deps import get_locks, get_repository, requiere_rol
from .schemas import (
    PromediosResponse,
    RegistrarResultadoRequest,
    ResultadoListItem,
    ResultadoResponse,
)

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
    locks: Annotated[KeyedLocks, Depends(get_locks)],
) -> ResultadoResponse:
    evaluacion = Evaluacion(
        evaluado_id=body.evaluado_id,
        fecha_del_test=body.fecha_del_test.isoformat(),
        titulo=body.titulo,
        competencias=body.competencias.model_dump(),
    )
    caso = RegistrarResultado(repo, locks)
    try:
        url, resultado = await caso.ejecutar(evaluacion)
    except EvaluadoInexistenteError as exc:
        # 422 literal: el nombre HTTP_422_* fue renombrado/deprecado en Starlette reciente.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ResultadoDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except NotionUnavailableError as exc:
        # No filtrar detalles internos (A10).
        logger.warning("Notion no disponible al registrar resultado")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servicio de persistencia no disponible. Reintenta más tarde.",
        ) from exc
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


@router.get(
    "/v1/resultados",
    response_model=list[ResultadoListItem],
    tags=["resultados"],
)
async def listar_resultados(
    principal: Annotated[Principal, Depends(requiere_rol("evaluador", "lector"))],
    repo: Annotated[ResultRepository, Depends(get_repository)],
    evaluado_id: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ResultadoListItem]:
    caso = ListarResultadosPorEvaluado(repo)
    try:
        filas = await caso.ejecutar(evaluado_id, limit)
    except NotionUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servicio de persistencia no disponible.",
        ) from exc
    return [ResultadoListItem(**f) for f in filas]
