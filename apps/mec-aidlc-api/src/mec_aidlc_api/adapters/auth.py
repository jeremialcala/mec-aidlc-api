"""Verificación de JWT OAuth2 — IdP: Auth0 (ADR-0003).

Controles: fija algoritmos permitidos (evita `alg=none`), verifica firma, exp, iss y aud
(A07/A01). En producción usa el JWKS de Auth0 (RS256); el modo secreto compartido HS256 es
solo para desarrollo local. Los roles se leen del claim con namespace de Auth0.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from ..config import Settings


class AuthError(Exception):
    """Token ausente, inválido, expirado o con claims incorrectos."""


@dataclass(frozen=True)
class Principal:
    """Identidad autenticada extraída del token."""

    sub: str
    roles: list[str]


class JwtVerifier:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._jwks_client: PyJWKClient | None = (
            PyJWKClient(settings.jwt_jwks_url) if settings.jwt_jwks_url else None
        )

    def verificar(self, token: str) -> Principal:
        # Exige exp siempre; iss/aud como claims requeridos cuando están configurados.
        require = ["exp"]
        if self._s.jwt_issuer:
            require.append("iss")
        if self._s.jwt_audience:
            require.append("aud")
        options = {"require": require}
        try:
            if self._jwks_client is not None:
                # Producción (Auth0): iss y aud son obligatorios; fail-closed si faltan (T1/T3).
                if not (self._s.jwt_issuer and self._s.jwt_audience):
                    raise AuthError(
                        "Config JWT incompleta: iss y aud son obligatorios con JWKS."
                    )
                signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
                claims = jwt.decode(
                    token,
                    signing_key,
                    algorithms=self._s.jwt_algorithms_list,
                    audience=self._s.jwt_audience,
                    issuer=self._s.jwt_issuer,
                    options=options,
                )
            elif self._s.jwt_dev_shared_secret:
                # Desarrollo local: HS256 con secreto compartido.
                claims = jwt.decode(
                    token,
                    self._s.jwt_dev_shared_secret,
                    algorithms=["HS256"],
                    audience=self._s.jwt_audience or None,
                    issuer=self._s.jwt_issuer or None,
                    options=options,
                )
            else:
                raise AuthError(
                    "Verificación JWT no configurada (falta JWKS o secreto de desarrollo)."
                )
        except jwt.PyJWTError as exc:  # firma, exp, iss, aud, etc.
            raise AuthError(f"Token inválido: {exc}") from exc

        sub = claims.get("sub")
        if not sub:
            raise AuthError("Token sin 'sub'.")
        roles = _extraer_roles(claims, self._s.jwt_roles_claim)
        return Principal(sub=str(sub), roles=roles)


def _extraer_roles(claims: dict, roles_claim: str = "") -> list[str]:
    """Extrae roles del claim configurado (Auth0 usa namespace) con fallbacks comunes."""
    # 1. Claim explícito (Auth0 Action, p. ej. 'https://mec-aidlc/roles').
    if roles_claim and isinstance(claims.get(roles_claim), list):
        return [str(r) for r in claims[roles_claim]]
    # 2. Claim 'roles' plano.
    if isinstance(claims.get("roles"), list):
        return [str(r) for r in claims["roles"]]
    # 3. Keycloak: realm_access.roles.
    realm = claims.get("realm_access") or {}
    if isinstance(realm.get("roles"), list):
        return [str(r) for r in realm["roles"]]
    # 4. Auth0 RBAC: 'permissions' en el access token.
    if isinstance(claims.get("permissions"), list):
        return [str(r) for r in claims["permissions"]]
    return []
