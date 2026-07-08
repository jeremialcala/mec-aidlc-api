"""Dependencias de FastAPI: autenticación, autorización por rol y repositorio."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..adapters.auth import AuthError, JwtVerifier, Principal
from ..config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_verifier(request: Request) -> JwtVerifier:
    """El verificador JWT (con su caché de JWKS) se crea una vez en el lifespan."""
    return request.app.state.verifier


def get_principal(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    verifier: Annotated[JwtVerifier, Depends(get_verifier)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Principal:
    # auth_disabled es SOLO para desarrollo local (ver config / ADR-0003).
    if settings.auth_disabled:
        return Principal(sub="dev-local", roles=["evaluador", "lector"])
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verifier.verificar(creds.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def requiere_rol(*roles_permitidos: str):
    """Factory de dependencia RBAC deny-by-default (A01)."""

    def _dep(
        principal: Annotated[Principal, Depends(get_principal)],
    ) -> Principal:
        if not set(roles_permitidos) & set(principal.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rol insuficiente para esta operación.",
            )
        return principal

    return _dep


def get_repository(request: Request):
    """El repositorio Notion se crea una vez y vive en app.state (lifespan)."""
    return request.app.state.repository


def get_locks(request: Request):
    """Locks por clave compartidos (creados una vez en el lifespan)."""
    return request.app.state.locks
