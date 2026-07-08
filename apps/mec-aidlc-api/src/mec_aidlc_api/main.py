"""Punto de entrada de la API MEC-AIDLC (FastAPI)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .adapters.auth import JwtVerifier
from .adapters.notion_repository import NotionResultRepository
from .api.routes import router
from .application.concurrency import KeyedLocks
from .config import get_settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.validar_seguridad()  # fail-closed si la config de auth es insegura en prod (M2)
    app.state.repository = NotionResultRepository(settings)
    app.state.locks = KeyedLocks()
    # Un único verificador JWT: reutiliza la caché de JWKS entre peticiones (ADR-0003).
    app.state.verifier = JwtVerifier(settings)
    try:
        yield
    finally:
        await app.state.repository.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MEC-AIDLC API",
        version="0.1.0",
        description="Registra resultados de la evaluación MEC-AIDLC en Notion.",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
