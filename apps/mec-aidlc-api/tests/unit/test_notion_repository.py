"""Tests del adaptador Notion: reintento con backoff e idempotencia (T6/T7).

Usa httpx.MockTransport para simular respuestas de Notion sin red.
"""
import json

import httpx
import pytest

from mec_aidlc_api.adapters.notion_repository import (
    NOTION_API,
    NotionResultRepository,
    NotionUnavailableError,
)
from mec_aidlc_api.config import Settings
from mec_aidlc_api.domain import scoring
from mec_aidlc_api.domain.models import COMPETENCIA_A_DOMINIO, Evaluacion


def _settings(**over):
    base = dict(
        notion_token="test-token",
        notion_max_reintentos=2,
        notion_backoff_base_s=0.0,
        notion_backoff_max_s=0.0,
    )
    base.update(over)
    return Settings(**base)


def _repo(handler, **settings_over):
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=NOTION_API,
        headers={"Authorization": "Bearer test-token"},
    )
    return NotionResultRepository(_settings(**settings_over), client=client)


def _evaluacion():
    comps = {k: 3 for k in COMPETENCIA_A_DOMINIO}
    return Evaluacion(
        evaluado_id="e1", fecha_del_test="2026-07-08", titulo="Q3", competencias=comps
    )


def _es_pages(request: httpx.Request) -> bool:
    return request.url.path.endswith("/pages")


async def test_guardar_reintenta_tras_429_y_tiene_exito():
    n = {"pages": 0}

    def handler(request):
        if _es_pages(request):
            n["pages"] += 1
            if n["pages"] == 1:
                return httpx.Response(429, headers={"Retry-After": "0"}, json={})
            return httpx.Response(200, json={"url": "https://notion.so/ok"})
        return httpx.Response(200, json={"results": []})  # recheck: aún no existe

    repo = _repo(handler)
    ev = _evaluacion()
    url = await repo.guardar(ev, scoring.evaluar(ev.competencias))
    assert url == "https://notion.so/ok"
    assert n["pages"] == 2
    await repo.aclose()


async def test_guardar_agota_reintentos_y_lanza_unavailable():
    def handler(request):
        if _es_pages(request):
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"results": []})

    repo = _repo(handler)
    ev = _evaluacion()
    with pytest.raises(NotionUnavailableError):
        await repo.guardar(ev, scoring.evaluar(ev.competencias))
    await repo.aclose()


async def test_guardar_idempotente_no_duplica_si_creacion_previa_entro():
    # La creación "entra" en Notion pero la respuesta se pierde (timeout); el recheck la halla.
    n = {"pages": 0}

    def handler(request):
        if _es_pages(request):
            n["pages"] += 1
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, json={"results": [{"url": "https://notion.so/ya"}]})

    repo = _repo(handler)
    ev = _evaluacion()
    url = await repo.guardar(ev, scoring.evaluar(ev.competencias))
    assert url == "https://notion.so/ya"
    assert n["pages"] == 1  # no reintentó crear: el recheck cortó el bucle
    await repo.aclose()


async def test_guardar_4xx_no_transitorio_es_unavailable():
    # Un 401/400 de Notion (token/permiso/esquema) → 502 controlado, no 500, y sin reintentar (M1).
    n = {"pages": 0}

    def handler(request):
        if request.url.path.endswith("/pages"):
            n["pages"] += 1
            return httpx.Response(401, json={"message": "unauthorized"})
        return httpx.Response(200, json={"results": []})

    repo = _repo(handler)
    ev = _evaluacion()
    with pytest.raises(NotionUnavailableError):
        await repo.guardar(ev, scoring.evaluar(ev.competencias))
    assert n["pages"] == 1  # un 4xx no es transitorio: no se reintenta
    await repo.aclose()


async def test_lectura_reintenta_en_error_transitorio():
    n = {"q": 0}

    def handler(request):
        n["q"] += 1
        if n["q"] == 1:
            return httpx.Response(500, json={})
        return httpx.Response(200, json={"results": [{"id": "1", "url": "u"}]})

    repo = _repo(handler)
    out = await repo.listar_por_evaluado("e1")
    assert out == [{"id": "1", "url": "u"}]
    assert n["q"] == 2
    await repo.aclose()


# --- Validación del evaluado contra la BD Fichas (esc. #5, ADR-0007) ---


async def test_evaluado_existe_sin_config_omite_validacion():
    def handler(request):  # no debería llamarse
        raise AssertionError("no debe consultar Notion sin BD de fichas")

    repo = _repo(handler)  # notion_fichas_data_source_id vacío
    assert await repo.evaluado_existe("x") is True
    await repo.aclose()


async def test_evaluado_existe_true_si_ficha_en_la_bd():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path.endswith("/pages/page-1")
        return httpx.Response(200, json={"parent": {"data_source_id": "fichas-ds"}})

    repo = _repo(handler, notion_fichas_data_source_id="fichas-ds")
    assert await repo.evaluado_existe("page-1") is True
    await repo.aclose()


async def test_evaluado_existe_false_si_404():
    repo = _repo(
        lambda request: httpx.Response(404, json={}),
        notion_fichas_data_source_id="fichas-ds",
    )
    assert await repo.evaluado_existe("inexistente") is False
    await repo.aclose()


async def test_evaluado_existe_false_si_ficha_de_otra_bd():
    def handler(request):
        return httpx.Response(200, json={"parent": {"data_source_id": "otra-bd"}})

    repo = _repo(handler, notion_fichas_data_source_id="fichas-ds")
    assert await repo.evaluado_existe("page-1") is False
    await repo.aclose()


# --- Contrato con la API de Notion (A1: data sources requiere versión moderna) ---


async def test_cliente_declara_version_de_data_sources():
    # El cliente real debe enviar una Notion-Version que soporte data sources (>= 2025-09-03).
    repo = NotionResultRepository(_settings())  # client real; no hay red hasta hacer un request
    assert repo._client.headers.get("Notion-Version") == "2025-09-03"
    await repo.aclose()


async def test_contrato_rutas_y_parent_data_source():
    reqs = []

    def handler(request):
        reqs.append(request)
        if request.url.path.endswith("/pages"):
            return httpx.Response(200, json={"url": "u"})
        return httpx.Response(200, json={"results": []})

    repo = _repo(handler)
    ev = _evaluacion()
    ds = repo._s.notion_data_source_id
    await repo.existe(ev.evaluado_id, ev.fecha_del_test)
    await repo.guardar(ev, scoring.evaluar(ev.competencias))
    paths = [r.url.path for r in reqs]
    # La consulta usa el endpoint de data sources.
    assert any(p.endswith(f"/data_sources/{ds}/query") for p in paths)
    # La creación usa parent data_source_id (no database_id).
    create = next(r for r in reqs if r.url.path.endswith("/pages"))
    assert json.loads(create.content)["parent"] == {"data_source_id": ds}
    await repo.aclose()
