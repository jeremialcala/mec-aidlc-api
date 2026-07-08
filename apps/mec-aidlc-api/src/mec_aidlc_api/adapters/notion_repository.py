"""Adaptador de persistencia contra la API de Notion (ADR-0002).

Escribe SOLO campos editables; nunca los campos fórmula (`Promedio D1–D4`, `IGV`, `Estadio`),
que Notion deriva. Maneja timeout y errores externos sin filtrar detalles internos (A10).
"""
from __future__ import annotations

import httpx

from ..config import Settings
from ..domain.models import COMPETENCIA_A_NOTION, Evaluacion, ResultadoEvaluacion

NOTION_API = "https://api.notion.com/v1"


class NotionUnavailableError(Exception):
    """Notion no disponible / error de red / rate-limit (A10)."""


class NotionResultRepository:
    """Implementa el puerto ResultRepository sobre la API de Notion."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._s = settings
        self._client = client or httpx.AsyncClient(
            base_url=NOTION_API,
            timeout=settings.notion_timeout_s,
            headers={
                "Authorization": f"Bearer {settings.notion_token}",
                "Notion-Version": settings.notion_version,
                "Content-Type": "application/json",
            },
        )

    async def existe(self, evaluado_id: str, fecha_del_test: str) -> bool:
        payload = {
            "filter": {
                "and": [
                    {
                        "property": self._s.notion_evaluado_property,
                        "relation": {"contains": evaluado_id},
                    },
                    {
                        "property": "Fecha del test",
                        "date": {"equals": fecha_del_test},
                    },
                ]
            },
            "page_size": 1,
        }
        data = await self._post(
            f"/data_sources/{self._s.notion_data_source_id}/query", payload
        )
        return bool(data.get("results"))

    async def guardar(
        self, evaluacion: Evaluacion, resultado: ResultadoEvaluacion
    ) -> str:
        props: dict = {
            "Resultado": {"title": [{"text": {"content": evaluacion.titulo}}]},
            self._s.notion_evaluado_property: {
                "relation": [{"id": evaluacion.evaluado_id}]
            },
            "Fecha del test": {"date": {"start": evaluacion.fecha_del_test}},
            "Diagnóstico": {
                "rich_text": [{"text": {"content": resultado.patron_diagnostico}}]
            },
            "Estado": {"status": {"name": "Done"}},
        }
        # 16 competencias como number. NO se escriben campos fórmula.
        for clave, valor in evaluacion.competencias.items():
            props[COMPETENCIA_A_NOTION[clave]] = {"number": valor}

        body = {
            "parent": {"data_source_id": self._s.notion_data_source_id},
            "properties": props,
        }
        data = await self._post("/pages", body)
        return data.get("url", "")

    async def listar_por_evaluado(self, evaluado_id: str) -> list[dict]:
        payload = {
            "filter": {
                "property": self._s.notion_evaluado_property,
                "relation": {"contains": evaluado_id},
            }
        }
        data = await self._post(
            f"/data_sources/{self._s.notion_data_source_id}/query", payload
        )
        return [
            {"id": r.get("id"), "url": r.get("url")} for r in data.get("results", [])
        ]

    async def _post(self, path: str, json_body: dict) -> dict:
        try:
            resp = await self._client.post(path, json=json_body)
        except httpx.HTTPError as exc:
            raise NotionUnavailableError("No se pudo contactar Notion.") from exc
        if resp.status_code == 429 or resp.status_code >= 500:
            raise NotionUnavailableError(
                f"Notion respondió {resp.status_code}."
            )
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()
