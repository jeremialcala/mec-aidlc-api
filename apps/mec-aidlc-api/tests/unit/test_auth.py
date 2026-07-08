"""Tests de verificación y extracción de roles del JWT (Auth0/dev) — ADR-0003."""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from mec_aidlc_api.adapters.auth import AuthError, JwtVerifier, _extraer_roles
from mec_aidlc_api.config import Settings

ISS = "https://tenant.auth0.com/"
AUD = "https://mec-aidlc-api"
ROLES_CLAIM = "https://mec-aidlc/roles"
SECRET = "dev-secret-para-tests-0123456789abcdef"  # >=32 bytes (evita warning HMAC)


def _settings(**over):
    base = dict(
        notion_token="t",
        jwt_dev_shared_secret=SECRET,
        jwt_issuer=ISS,
        jwt_audience=AUD,
        jwt_roles_claim=ROLES_CLAIM,
    )
    base.update(over)
    return Settings(**base)


def _token(**over):
    claims = {
        "sub": "auth0|u1",
        "iss": ISS,
        "aud": AUD,
        "exp": int(time.time()) + 3600,
        ROLES_CLAIM: ["evaluador"],
    }
    claims.update(over)
    # Permite omitir claims pasando None.
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_roles_desde_claim_con_namespace_auth0():
    # Auth0 añade los roles vía Action en un claim con namespace.
    claims = {"https://mec-aidlc/roles": ["evaluador"]}
    assert _extraer_roles(claims, "https://mec-aidlc/roles") == ["evaluador"]


def test_roles_desde_permissions_rbac_auth0():
    # Auth0 RBAC: los permisos llegan en el claim 'permissions'.
    claims = {"permissions": ["lector"]}
    assert _extraer_roles(claims) == ["lector"]


def test_roles_claim_plano_y_keycloak():
    assert _extraer_roles({"roles": ["evaluador", "lector"]}) == ["evaluador", "lector"]
    assert _extraer_roles({"realm_access": {"roles": ["evaluador"]}}) == ["evaluador"]


def test_sin_roles_devuelve_vacio():
    # Un token Auth0 sin la Action de roles no otorga acceso (RBAC deny-by-default).
    assert _extraer_roles({"sub": "abc"}, "https://mec-aidlc/roles") == []


def test_verifica_token_valido_y_extrae_roles():
    principal = JwtVerifier(_settings()).verificar(_token())
    assert principal.sub == "auth0|u1"
    assert principal.roles == ["evaluador"]


def test_rechaza_audiencia_incorrecta():
    with pytest.raises(AuthError):
        JwtVerifier(_settings()).verificar(_token(aud="otra-api"))


def test_rechaza_emisor_incorrecto():
    with pytest.raises(AuthError):
        JwtVerifier(_settings()).verificar(_token(iss="https://malicioso/"))


def test_rechaza_token_sin_exp():
    with pytest.raises(AuthError):
        JwtVerifier(_settings()).verificar(_token(exp=None))


def test_rechaza_token_expirado():
    with pytest.raises(AuthError):
        JwtVerifier(_settings()).verificar(_token(exp=int(time.time()) - 10))


def test_rechaza_alg_none():
    # Token sin firma (alg=none): los algoritmos permitidos están fijados → se rechaza (T3).
    payload = {"sub": "u", "iss": ISS, "aud": AUD, "exp": int(time.time()) + 100}
    tok = jwt.encode(payload, None, algorithm="none")
    with pytest.raises(AuthError):
        JwtVerifier(_settings()).verificar(tok)


# --- Rama de PRODUCCIÓN: RS256 verificado contra JWKS (M4) ---

_RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _FakeJwk:
    def __init__(self, key):
        self.key = key


class _FakeJwksClient:
    """Sustituye al PyJWKClient real: devuelve la clave pública de test sin tocar la red."""

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return _FakeJwk(self._public_key)


def _rsa_verifier(**over):
    base = dict(
        notion_token="t",
        jwt_jwks_url="https://tenant.auth0.com/.well-known/jwks.json",
        jwt_issuer=ISS,
        jwt_audience=AUD,
        jwt_roles_claim=ROLES_CLAIM,
    )
    base.update(over)
    verifier = JwtVerifier(Settings(**base))
    verifier._jwks_client = _FakeJwksClient(_RSA_KEY.public_key())
    return verifier


def _rs256_token(**over):
    claims = {
        "sub": "auth0|u1",
        "iss": ISS,
        "aud": AUD,
        "exp": int(time.time()) + 3600,
        ROLES_CLAIM: ["evaluador"],
    }
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, _RSA_KEY, algorithm="RS256")


def test_jwks_rs256_token_valido():
    principal = _rsa_verifier().verificar(_rs256_token())
    assert principal.sub == "auth0|u1"
    assert principal.roles == ["evaluador"]


def test_jwks_rechaza_alg_none():
    # Aunque el token no esté firmado, la lista de algoritmos permitidos (RS256) lo rechaza.
    tok = jwt.encode(
        {"sub": "u", "iss": ISS, "aud": AUD, "exp": int(time.time()) + 100},
        None,
        algorithm="none",
    )
    with pytest.raises(AuthError):
        _rsa_verifier().verificar(tok)


def test_jwks_rechaza_audiencia_incorrecta():
    with pytest.raises(AuthError):
        _rsa_verifier().verificar(_rs256_token(aud="otra-api"))


def test_jwks_fail_closed_sin_iss_aud():
    # Con JWKS configurado pero sin iss/aud → fail-closed (no verifica).
    with pytest.raises(AuthError):
        _rsa_verifier(jwt_issuer="", jwt_audience="").verificar(_rs256_token())
