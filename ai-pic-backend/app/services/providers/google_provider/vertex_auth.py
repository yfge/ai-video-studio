"""
Vertex AI OAuth access token helper.

Uses a service account (JSON string or file) to mint short-lived tokens
with caching to reduce token endpoint traffic.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from app.core.logging import get_logger
from jose import jwt

DEFAULT_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_APPLICATION_CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"


@dataclass
class CachedAccessToken:
    access_token: str
    expires_at: float

    def is_valid(self, leeway: float = 60.0) -> bool:
        return bool(self.access_token) and (self.expires_at - leeway) > time.time()


def load_service_account_info(
    *,
    service_account_json: Optional[str],
    service_account_path: Optional[str],
    logger: Any,
) -> Optional[Dict[str, Any]]:
    if service_account_json:
        try:
            info = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid Vertex service account JSON: %s", exc)
        else:
            return _validate_service_account_info(info, logger)

    path = service_account_path or os.getenv(GOOGLE_APPLICATION_CREDENTIALS_ENV)
    if not path:
        return None

    try:
        with open(path, "r", encoding="utf-8") as handle:
            info = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read Vertex service account file: %s", exc)
        return None
    return _validate_service_account_info(info, logger)


def _validate_service_account_info(
    info: Dict[str, Any],
    logger: Any,
) -> Optional[Dict[str, Any]]:
    if not isinstance(info, dict):
        logger.warning("Vertex service account payload must be a JSON object")
        return None
    if not info.get("client_email") or not info.get("private_key"):
        logger.warning("Vertex service account JSON missing client_email/private_key")
        return None
    return info


def build_service_account_assertion(
    *,
    service_account_info: Dict[str, Any],
    scope: str,
    token_uri: str,
    now: Optional[int] = None,
) -> Optional[str]:
    issued_at = int(now or time.time())
    payload = {
        "iss": service_account_info.get("client_email"),
        "scope": scope,
        "aud": token_uri,
        "iat": issued_at,
        "exp": issued_at + 3600,
    }
    try:
        return jwt.encode(
            payload,
            service_account_info.get("private_key"),
            algorithm="RS256",
            headers={"typ": "JWT"},
        )
    except Exception:
        return None


async def request_access_token(
    *,
    token_uri: str,
    assertion: str,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            token_uri,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        resp.raise_for_status()
        return resp.json()


class VertexAccessTokenProvider:
    def __init__(
        self,
        *,
        service_account_info: Dict[str, Any],
        scope: str = DEFAULT_SCOPE,
        token_uri: Optional[str] = None,
        logger: Any = None,
    ) -> None:
        self._info = service_account_info
        self._scope = scope
        self._token_uri = token_uri or self._info.get("token_uri") or DEFAULT_TOKEN_URI
        self._logger = logger or get_logger(__name__)
        self._token_cache: Optional[CachedAccessToken] = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> Optional[str]:
        cached = self._token_cache
        if cached and cached.is_valid():
            return cached.access_token

        async with self._lock:
            cached = self._token_cache
            if cached and cached.is_valid():
                return cached.access_token
            return await self._refresh_token()

    async def _refresh_token(self) -> Optional[str]:
        assertion = build_service_account_assertion(
            service_account_info=self._info,
            scope=self._scope,
            token_uri=self._token_uri,
        )
        if not assertion:
            self._logger.warning("Vertex OAuth assertion generation failed")
            return None

        try:
            payload = await request_access_token(
                token_uri=self._token_uri,
                assertion=assertion,
            )
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("Vertex OAuth token refresh failed: %s", exc)
            return None

        token = payload.get("access_token")
        if not token:
            self._logger.warning("Vertex OAuth response missing access_token")
            return None

        expires_in = payload.get("expires_in", 3600)
        try:
            expires_in_value = int(expires_in)
        except (TypeError, ValueError):
            expires_in_value = 3600
        self._token_cache = CachedAccessToken(
            access_token=token,
            expires_at=time.time() + max(expires_in_value, 0),
        )
        return token


def build_vertex_access_token_provider(
    *,
    service_account_json: Optional[str],
    service_account_path: Optional[str],
    logger: Any = None,
) -> Optional[VertexAccessTokenProvider]:
    logger = logger or get_logger(__name__)
    info = load_service_account_info(
        service_account_json=service_account_json,
        service_account_path=service_account_path,
        logger=logger,
    )
    if not info:
        return None
    return VertexAccessTokenProvider(service_account_info=info, logger=logger)
