"""
MiniMax API client

Unified low-level HTTP client for MiniMax APIs (text, voice, music).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class MinimaxAPIError(Exception):
    """Custom exception for MiniMax API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        trace_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id


class MinimaxClient:
    """Reusable async client for MiniMax APIs."""

    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"

    def __init__(
        self,
        api_key: str,
        group_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.group_id = group_id
        self.base_url = self._normalize_base_url(base_url or self.DEFAULT_BASE_URL)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._loop_id: Optional[int] = None

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if not normalized.endswith("/v1"):
            normalized = f"{normalized}/v1"
        return normalized

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.group_id:
            headers["GroupId"] = self.group_id
        return headers

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    async def get_client(self) -> httpx.AsyncClient:
        """Return a loop-safe AsyncClient instance."""
        try:
            loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            loop_id = None

        if (
            self._client is None
            or getattr(self._client, "is_closed", False)
            or (loop_id is not None and self._loop_id != loop_id)
        ):
            self._client = httpx.AsyncClient(
                timeout=self.timeout, headers=self._build_headers()
            )
            self._loop_id = loop_id
        return self._client

    def _raise_for_status(self, payload: Dict[str, Any]) -> None:
        base_resp = payload.get("base_resp")
        if isinstance(base_resp, dict):
            status_code = base_resp.get("status_code")
            if status_code not in (0, None):
                raise MinimaxAPIError(
                    base_resp.get("status_msg") or "MiniMax API error",
                    status_code=status_code,
                    trace_id=payload.get("trace_id") or payload.get("traceId"),
                )

    async def post_json(
        self, path: str, payload: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        client = await self.get_client()
        response = await client.post(
            self._build_url(path), json=payload or {}, **kwargs
        )
        response.raise_for_status()
        body = response.json()
        self._raise_for_status(body)
        return body

    async def close(self) -> None:
        if self._client and not getattr(self._client, "is_closed", False):
            await self._client.aclose()
