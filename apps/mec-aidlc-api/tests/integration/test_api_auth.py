"""Tests de auth a nivel HTTP con auth ACTIVADA (ruta HS256 de desarrollo).

Cubre los escenarios de abuso del PRD: 1 (401 sin token / inválido / expirado),
2 (403 por rol) y 9 (firma manipulada). Se sobreescribe `get_settings` para activar
la verificación JWT sin depender de variables de entorno.
"""
import os
import time

import jwt
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DATA_SOURCE_ID", "ds-test")

from mec_aidlc_api.adapters.auth import JwtVerifier  # noqa: E402
from mec_aidlc_api.config import Settings, get_settings  # noqa: E402
from mec_aidlc_api.main import create_app  # noqa: E402

ISS = "https://tenant.auth0.com/"
AUD = "https://mec-aidlc-api"
ROLES_CLAIM = "https://mec-aidlc/roles"
SECRET = "dev-secret-para-tests-0123456789abcdef"  # >=32 bytes


def _settings():
    return Settings(
        notion_token="t",
        auth_disabled=False,
        jwt_dev_shared_secret=SECRET,
        jwt_issuer=ISS,
        jwt_audience=AUD,
        jwt_roles_claim=ROLES_CLAIM,
    )


def _token(roles=("evaluador",), secret=SECRET, **over):
    claims = {
        "sub": "auth0|u1",
        "iss": ISS,
        "aud": AUD,
        "exp": int(time.time()) + 3600,
        ROLES_CLAIM: list(roles),
    }
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, secret, algorithm="HS256")


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class _FakeRepo:
    async def existe(self, *a):
        return False

    async def evaluado_existe(self, *a):
        return True

    async def guardar(self, *a):
        return "https://www.notion.so/fake"

    async def listar_por_evaluado(self, *a):
        return []

    async def aclose(self):
        return None


def _payload():
    comps = {k: 3 for k in [
        "conocimientos_tecnicos", "pensamiento_analitico", "pensamiento_conceptual",
        "toma_de_decisiones", "orientacion_a_resultados", "productividad",
        "planificacion_y_organizacion", "gestion_y_logro_de_objetivos",
        "trabajo_en_equipo", "colaboracion", "comunicacion_eficaz",
        "influencia_y_negociacion", "adaptabilidad_a_los_cambios",
        "iniciativa_y_autonomia", "desarrollo_y_autodesarrollo", "etica_en_el_uso_de_ia",
    ]}
    return {
        "evaluado_id": "page-123",
        "fecha_del_test": "2026-07-08",
        "titulo": "Q3",
        "competencias": comps,
    }


@pytest.fixture
async def client():
    app = create_app()
    app.dependency_overrides[get_settings] = _settings
    async with LifespanManager(app):
        app.state.repository = _FakeRepo()
        app.state.verifier = JwtVerifier(_settings())  # verificador con la config de auth del test
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()


# --- Escenario 1: sin token / inválido / expirado → 401 ---


async def test_post_sin_token_es_401(client):
    r = await client.post("/v1/resultados", json=_payload())
    assert r.status_code == 401


async def test_get_sin_token_es_401(client):
    r = await client.get("/v1/resultados", params={"evaluado_id": "page-123"})
    assert r.status_code == 401


async def test_token_basura_es_401(client):
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth("no-es-jwt"))
    assert r.status_code == 401


async def test_token_expirado_es_401(client):
    tok = _token(exp=int(time.time()) - 3600)  # más allá del leeway de reloj (B5)
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth(tok))
    assert r.status_code == 401


# --- Escenario 9: firma manipulada (secreto incorrecto) → 401 ---


async def test_token_firma_invalida_es_401(client):
    tok = _token(secret="otro-secreto-incorrecto-0123456789abcd")
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth(tok))
    assert r.status_code == 401


# --- Escenario 2: RBAC por rol ---


async def test_lector_no_puede_registrar_es_403(client):
    tok = _token(roles=("lector",))
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth(tok))
    assert r.status_code == 403


async def test_token_sin_roles_es_403(client):
    tok = _token(roles=())
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth(tok))
    assert r.status_code == 403


async def test_evaluador_puede_registrar_es_201(client):
    tok = _token(roles=("evaluador",))
    r = await client.post("/v1/resultados", json=_payload(), headers=_auth(tok))
    assert r.status_code == 201


async def test_lector_puede_consultar_es_200(client):
    tok = _token(roles=("lector",))
    r = await client.get(
        "/v1/resultados", params={"evaluado_id": "page-123"}, headers=_auth(tok)
    )
    assert r.status_code == 200


async def test_health_no_requiere_auth(client):
    r = await client.get("/health")
    assert r.status_code == 200
