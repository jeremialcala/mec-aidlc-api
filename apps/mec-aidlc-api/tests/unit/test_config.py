"""Tests de la validación de seguridad de configuración en producción (M2)."""
import pytest

from mec_aidlc_api.config import Settings

_PROD_OK = dict(
    notion_token="t",
    app_env="prod",
    auth_disabled=False,
    jwt_jwks_url="https://tenant.auth0.com/.well-known/jwks.json",
    jwt_issuer="https://tenant.auth0.com/",
    jwt_audience="https://mec-aidlc-api",
    jwt_dev_shared_secret="",
)


def _settings(**over):
    base = dict(_PROD_OK)
    base.update(over)
    return Settings(**base)


def test_prod_config_segura_no_lanza():
    _settings().validar_seguridad()  # no debe lanzar


def test_prod_rechaza_auth_disabled():
    with pytest.raises(RuntimeError):
        _settings(auth_disabled=True).validar_seguridad()


def test_prod_requiere_jwks():
    with pytest.raises(RuntimeError):
        _settings(jwt_jwks_url="").validar_seguridad()


def test_prod_rechaza_secreto_dev():
    with pytest.raises(RuntimeError):
        _settings(jwt_dev_shared_secret="secreto-heredado").validar_seguridad()


def test_dev_no_valida():
    # En dev, aun con auth deshabilitada y sin JWKS, no falla el arranque.
    Settings(
        notion_token="t", app_env="dev", auth_disabled=True, jwt_jwks_url=""
    ).validar_seguridad()
