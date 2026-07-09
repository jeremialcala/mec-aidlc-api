"""Adaptador de persistencia contra la API de Notion (ADR-0002).

Escribe SOLO campos editables; nunca los campos fórmula (`Promedio D1–D4`, `IGV`, `Estadio`),
que Notion deriva. Ante errores transitorios (timeout, red, 429, 5xx) reintenta con backoff
exponencial (T6/A10). La creación de páginas es **idempotente**: tras un fallo transitorio
re-verifica por (evaluado, fecha) antes de reintentar, para no duplicar si la creación anterior
sí llegó a persistir (T7/A08). No filtra detalles internos en el error hacia el cliente.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from ..config import Settings
from ..domain.models import COMPETENCIA_A_NOTION, Evaluacion, ResultadoEvaluacion

NOTION_API = "https://api.notion.com/v1"

logger = logging.getLogger("mec_aidlc_api")


class NotionUnavailableError(Exception):
    """Notion no disponible / red / rate-limit tras agotar los reintentos (A10)."""


class _TransitorioError(Exception):
    """Error transitorio (timeout, red, 429, 5xx). Interno: dispara reintento."""

    def __init__(self, mensaje: str, retry_after: float | None = None) -> None:
        super().__init__(mensaje)
        self.retry_after = retry_after


class NotionResultRepository:
    """Implementa el puerto ResultRepository sobre la API de Notion."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        if not settings.notion_data_source_id:
            raise ValueError(
                "NOTION_DATA_SOURCE_ID es obligatorio (data source de resultados)."
            )
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
        # Lectura idempotente: reintenta ante errores transitorios.
        data = await self._query_con_reintentos(
            self._filtro_idempotencia(evaluado_id, fecha_del_test)
        )
        return bool(data.get("results"))

    async def evaluado_existe(self, evaluado_id: str) -> bool:
        """Valida el evaluado contra la BD 'Fichas' (solo lectura) — ADR-0007, esc. #5.

        Si no hay BD de fichas configurada, la validación se omite (dev/local); en producción
        debe configurarse `NOTION_FICHAS_DATA_SOURCE_ID`.
        """
        if not self._s.notion_fichas_data_source_id:
            return True
        resp = await self._get_ficha_con_reintentos(evaluado_id)
        if resp.status_code in (400, 404):
            return False  # id inexistente o malformado
        self._raise_si_error(resp)
        parent = resp.json().get("parent") or {}
        esperado = self._s.notion_fichas_data_source_id
        return esperado in (parent.get("data_source_id"), parent.get("database_id"))

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
            "Estado": {"status": {"name": self._s.notion_estado_done}},
        }
        # 16 competencias como number. NO se escriben campos fórmula.
        for clave, valor in evaluacion.competencias.items():
            props[COMPETENCIA_A_NOTION[clave]] = {"number": valor}

        body = {
            "parent": {"data_source_id": self._s.notion_data_source_id},
            "properties": props,
        }

        # Creación con reintento idempotente. `_post_once` no reintenta por sí solo porque un POST
        # no es idempotente: si un intento falla de forma transitoria la página podría haberse
        # creado igualmente, así que re-verificamos por (evaluado, fecha) antes de reintentar.
        ultimo: _TransitorioError | None = None
        for intento in range(self._s.notion_max_reintentos + 1):
            if intento > 0:
                await asyncio.sleep(self._backoff(intento, ultimo))
                url = await self._url_existente(evaluacion)
                if url is not None:
                    return url
            try:
                data = await self._post_once("/pages", body)
                return data.get("url", "")
            except _TransitorioError as exc:
                ultimo = exc
        # Último chequeo: quizá el intento final sí entró pese al error de respuesta.
        url = await self._url_existente(evaluacion)
        if url is not None:
            return url
        raise NotionUnavailableError("Notion no disponible al crear la página.") from ultimo

    async def listar_por_evaluado(self, evaluado_id: str) -> list[dict]:
        payload = {
            "filter": {
                "property": self._s.notion_evaluado_property,
                "relation": {"contains": evaluado_id},
            }
        }
        data = await self._query_con_reintentos(payload)
        return [
            {"id": r.get("id"), "url": r.get("url")} for r in data.get("results", [])
        ]

    # --- Helpers de idempotencia y transporte ---

    def _filtro_idempotencia(self, evaluado_id: str, fecha_del_test: str) -> dict:
        return {
            "filter": {
                "and": [
                    {
                        "property": self._s.notion_evaluado_property,
                        "relation": {"contains": evaluado_id},
                    },
                    {"property": "Fecha del test", "date": {"equals": fecha_del_test}},
                ]
            },
            "page_size": 1,
        }

    async def _url_existente(self, evaluacion: Evaluacion) -> str | None:
        """Un solo intento de lectura (sin reintentos anidados). None si no existe o si falla."""
        try:
            data = await self._post_once(
                f"/data_sources/{self._s.notion_data_source_id}/query",
                self._filtro_idempotencia(
                    evaluacion.evaluado_id, evaluacion.fecha_del_test
                ),
            )
        except _TransitorioError:
            return None  # no se pudo confirmar; se asume no creada y se reintenta
        resultados = data.get("results") or []
        return resultados[0].get("url", "") if resultados else None

    async def _query_con_reintentos(self, payload: dict) -> dict:
        path = f"/data_sources/{self._s.notion_data_source_id}/query"
        ultimo: _TransitorioError | None = None
        for intento in range(self._s.notion_max_reintentos + 1):
            if intento > 0:
                await asyncio.sleep(self._backoff(intento, ultimo))
            try:
                return await self._post_once(path, payload)
            except _TransitorioError as exc:
                ultimo = exc
        raise NotionUnavailableError(
            "No se pudo contactar Notion tras varios intentos."
        ) from ultimo

    async def _get_ficha_con_reintentos(self, page_id: str) -> httpx.Response:
        path = f"/pages/{page_id}"
        ultimo: _TransitorioError | None = None
        for intento in range(self._s.notion_max_reintentos + 1):
            if intento > 0:
                await asyncio.sleep(self._backoff(intento, ultimo))
            try:
                return await self._request_once("GET", path)
            except _TransitorioError as exc:
                ultimo = exc
        raise NotionUnavailableError(
            "No se pudo validar el evaluado en Notion."
        ) from ultimo

    async def _request_once(
        self, method: str, path: str, json_body: dict | None = None
    ) -> httpx.Response:
        try:
            resp = await self._client.request(method, path, json=json_body)
        except httpx.HTTPError as exc:
            raise _TransitorioError("Error de red al contactar Notion.") from exc
        if resp.status_code == 429:
            raise _TransitorioError("Notion respondió 429 (rate limit).", _retry_after(resp))
        if resp.status_code >= 500:
            raise _TransitorioError(f"Notion respondió {resp.status_code}.")
        return resp

    async def _post_once(self, path: str, json_body: dict) -> dict:
        resp = await self._request_once("POST", path, json_body)
        self._raise_si_error(resp)
        return resp.json()

    def _raise_si_error(self, resp: httpx.Response) -> None:
        """Un 4xx no transitorio (token/permiso/esquema/versión) es un fallo upstream, no del
        cliente: se mapea a 502 controlado sin volcar el cuerpo de Notion (A10)."""
        if resp.is_success:
            return
        logger.warning("Notion respondió %s (no transitorio)", resp.status_code)
        raise NotionUnavailableError(f"Notion respondió {resp.status_code}.")

    def _backoff(self, intento: int, exc: _TransitorioError | None) -> float:
        if exc is not None and exc.retry_after is not None:
            return min(exc.retry_after, self._s.notion_backoff_max_s)
        espera = self._s.notion_backoff_base_s * (2 ** (intento - 1))
        return min(espera, self._s.notion_backoff_max_s)

    async def aclose(self) -> None:
        await self._client.aclose()


def _retry_after(resp: httpx.Response) -> float | None:
    valor = resp.headers.get("Retry-After")
    if valor is None:
        return None
    try:
        return float(valor)
    except ValueError:
        return None
