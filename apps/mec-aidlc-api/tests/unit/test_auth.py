"""Tests de extracción de roles del JWT (Auth0 y fallbacks) — ADR-0003."""
from mec_aidlc_api.adapters.auth import _extraer_roles


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
