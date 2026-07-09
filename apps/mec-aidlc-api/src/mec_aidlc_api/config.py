"""Configuración cargada desde variables de entorno (ADR-0005).

Ningún secreto vive en el código. `.env` está en `.gitignore`; usa `.env.example` como guía.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Notion (ADR-0002 / ADR-0005) ---
    notion_token: str = Field(..., description="Token de integración Notion (secreto)")
    notion_data_source_id: str = Field(
        default="",
        description="Data source 'Resultados Test MEC-AIDLC' (requerido; se configura por entorno)",
    )
    notion_fichas_data_source_id: str = Field(
        default="",
        description="BD 'Fichas' para validar el evaluado (ADR-0007); vacío = sin validación",
    )
    notion_evaluado_property: str = Field(default="Evaluado")
    notion_estado_done: str = Field(
        default="Done", description="Opción de la propiedad 'Estado' (esquema de la BD)"
    )
    # La API de data sources (parent data_source_id, /data_sources/query) requiere >= 2025-09-03.
    notion_version: str = Field(default="2025-09-03")
    notion_timeout_s: float = Field(default=10.0)
    notion_max_reintentos: int = Field(
        default=2, description="Reintentos ante error transitorio (429/5xx/red) — T6/A10"
    )
    notion_backoff_base_s: float = Field(
        default=0.2, description="Base del backoff exponencial entre reintentos (s)"
    )
    notion_backoff_max_s: float = Field(
        default=5.0, description="Tope del backoff por intento (s)"
    )

    # --- Auth OAuth2 + JWT: Auth0 (ADR-0003) ---
    # iss = dominio del tenant Auth0 (con barra final); aud = identificador de la API en Auth0.
    jwt_issuer: str = Field(
        default="", description="Emisor esperado (iss), p. ej. https://<tenant>.auth0.com/"
    )
    jwt_audience: str = Field(
        default="", description="Audiencia esperada (aud) = API identifier de Auth0"
    )
    jwt_jwks_url: str = Field(
        default="", description="JWKS del tenant Auth0 (.well-known/jwks.json)"
    )
    jwt_algorithms: str = Field(
        default="RS256", description="Algoritmos permitidos (Auth0 firma RS256)"
    )
    # Auth0 entrega los roles en un claim con namespace (Action) o en 'permissions' (RBAC).
    jwt_roles_claim: str = Field(
        default="",
        description="Claim de roles; Auth0 requiere namespace, p. ej. https://mec-aidlc/roles",
    )
    # Solo para pruebas locales; en prod usar JWKS del IdP.
    jwt_dev_shared_secret: str = Field(default="")
    auth_disabled: bool = Field(
        default=False, description="Solo para desarrollo local — NUNCA en prod"
    )

    # --- Entorno ---
    app_env: str = Field(default="dev", description="dev | prod (activa validaciones de seguridad)")

    @property
    def jwt_algorithms_list(self) -> list[str]:
        return [a.strip() for a in self.jwt_algorithms.split(",") if a.strip()]

    @property
    def es_produccion(self) -> bool:
        return self.app_env.strip().lower() in ("prod", "production")

    def validar_seguridad(self) -> None:
        """Fail-closed en producción ante una configuración de auth insegura (M2).

        Evita desplegar con auth deshabilitada o degradada a HS256 (secreto compartido) por
        error de configuración. No hace nada fuera de producción.
        """
        if not self.es_produccion:
            return
        if self.auth_disabled:
            raise RuntimeError("AUTH_DISABLED no puede ser true en producción.")
        if not self.jwt_jwks_url:
            raise RuntimeError(
                "En producción se requiere JWT_JWKS_URL (verificación RS256 vía JWKS)."
            )
        if self.jwt_dev_shared_secret:
            raise RuntimeError(
                "JWT_DEV_SHARED_SECRET debe estar vacío en producción (solo dev)."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
