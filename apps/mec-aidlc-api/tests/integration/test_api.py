"""Tests de la capa API con un repositorio en memoria (fake) y auth deshabilitada.

Cubre escenarios positivos y de abuso del PRD (validación de esquema, idempotencia).
"""
import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ["AUTH_DISABLED"] = "true"

from mec_aidlc_api.domain.models import Evaluacion, ResultadoEvaluacion  # noqa: E402
from mec_aidlc_api.main import create_app  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.guardados: list[tuple[Evaluacion, ResultadoEvaluacion]] = []

    async def existe(self, evaluado_id: str, fecha_del_test: str) -> bool:
        return any(
            e.evaluado_id == evaluado_id and e.fecha_del_test == fecha_del_test
            for e, _ in self.guardados
        )

    async def guardar(self, evaluacion, resultado) -> str:
        self.guardados.append((evaluacion, resultado))
        return "https://www.notion.so/fake-page"

    async def listar_por_evaluado(self, evaluado_id: str) -> list[dict]:
        return [{"id": "x", "url": "https://www.notion.so/fake-page"}]

    async def aclose(self) -> None:
        return None


def _payload(**over):
    comps = {k: 3 for k in [
        "conocimientos_tecnicos", "pensamiento_analitico", "pensamiento_conceptual",
        "toma_de_decisiones", "orientacion_a_resultados", "productividad",
        "planificacion_y_organizacion", "gestion_y_logro_de_objetivos",
        "trabajo_en_equipo", "colaboracion", "comunicacion_eficaz",
        "influencia_y_negociacion", "adaptabilidad_a_los_cambios",
        "iniciativa_y_autonomia", "desarrollo_y_autodesarrollo", "etica_en_el_uso_de_ia",
    ]}
    body = {
        "evaluado_id": "page-123",
        "fecha_del_test": "2026-07-08",
        "titulo": "Evaluación Q3",
        "competencias": comps,
    }
    body.update(over)
    return body


@pytest.fixture
async def client():
    app = create_app()
    async with LifespanManager(app):
        app.state.repository = FakeRepo()  # sustituye Notion por el fake
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def test_health_sin_auth(client):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_registrar_resultado_ok(client):
    r = await client.post("/v1/resultados", json=_payload())
    assert r.status_code == 201
    data = r.json()
    # Todos los dominios en B (3): IGV=3.0, %IGV≈66.67, estadio Generador de Valor.
    assert data["igv"] == 3.0
    assert data["igv_pct"] == 66.67
    assert data["estadio"] == "Generador de Valor"
    assert data["notion_page_url"].startswith("https://")


async def test_competencia_fuera_de_rango_es_422(client):
    bad = _payload()
    bad["competencias"]["colaboracion"] = 5  # > 4
    r = await client.post("/v1/resultados", json=bad)
    assert r.status_code == 422


async def test_competencia_no_entera_es_422(client):
    bad = _payload()
    bad["competencias"]["colaboracion"] = 2.5  # los ítems son grados enteros 1–4
    r = await client.post("/v1/resultados", json=bad)
    assert r.status_code == 422


async def test_campo_extra_es_422(client):
    bad = _payload(hacker="1=1")  # extra=forbid
    r = await client.post("/v1/resultados", json=bad)
    assert r.status_code == 422


async def test_duplicado_es_409(client):
    await client.post("/v1/resultados", json=_payload())
    r = await client.post("/v1/resultados", json=_payload())
    assert r.status_code == 409
