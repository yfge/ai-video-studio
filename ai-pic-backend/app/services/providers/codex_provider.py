"""ChatGPT Codex responses provider.

This provider mirrors the local Codex CLI calling shape: it reuses
`~/.codex/auth.json` and calls the ChatGPT Codex responses endpoint with a
streaming Responses API payload.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .codex_auth import CodexAuthError, read_codex_auth, refresh_codex_auth
from .codex_image import run_codex_image_generation
from .codex_models import (
    CODEX_IMAGE_MODEL_ID,
    DEFAULT_CODEX_TEXT_MODEL,
    build_codex_models,
)
from .codex_payload import build_codex_payload, parse_codex_sse

DEFAULT_CODEX_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
CODEX_IMAGE_TIMEOUT_SECONDS = 240.0

logger = get_logger(__name__)


class _CodexUnauthorized(Exception):
    """Raised on 401 so generate_text can refresh auth once."""


class CodexProvider(BaseProvider):
    """ChatGPT OAuth provider backed by the Codex responses endpoint."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.endpoint = (config.base_url or DEFAULT_CODEX_RESPONSES_URL).rstrip("/")
        self.auth_path = config.api_key or settings.CODEX_AUTH_PATH
        self.default_model = config.default_model or DEFAULT_CODEX_TEXT_MODEL
        self._token: str | None = None
        self._account_id: str | None = None

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_GENERATION, AIModelType.TEXT_TO_IMAGE]

    @property
    def available_models(self) -> List[ModelInfo]:
        return build_codex_models(self.default_model)

    async def _initialize_client(self):
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        self._reload_auth()

    async def fetch_remote_models(
        self, model_type: Optional[AIModelType] = None
    ) -> List[ModelInfo]:
        fallback = self.available_models
        if model_type:
            return [model for model in fallback if model.model_type == model_type]
        return fallback

    async def generate_text(
        self,
        prompt: str,
        model: str = DEFAULT_CODEX_TEXT_MODEL,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        json_schema: Optional[Dict] = None,
        **kwargs,
    ) -> AIResponse:
        model_id = model or self.default_model
        try:
            client = await self.get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if json_schema:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Return only valid JSON matching the requested schema."
                        ),
                    }
                )
            messages.append({"role": "user", "content": prompt})
            # The ChatGPT Codex endpoint rejects temperature and output-token fields.
            payload = build_codex_payload(
                messages=messages,
                model=model_id,
            )
            try:
                text, usage = await self._post(client, payload)
            except _CodexUnauthorized:
                self._recover_after_unauthorized()
                text, usage = await self._post(client, payload)

            return AIResponse(
                success=True,
                data=text,
                provider=self.name,
                model=model_id,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage=usage,
                metadata={"stream": True, "endpoint": "codex_responses"},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Codex generate_text error: %s", exc, exc_info=True)
            return AIResponse(
                success=False,
                error=self.format_error(exc),
                provider=self.name,
                model=model_id,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

    async def generate_image(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """Generate one image via the ChatGPT image_generation tool."""
        model_id = model or CODEX_IMAGE_MODEL_ID
        try:
            client = await self.get_client()

            async def _post(payload: dict[str, Any]) -> str:
                try:
                    return await self._post_raw(client, payload)
                except _CodexUnauthorized:
                    self._recover_after_unauthorized()
                    return await self._post_raw(client, payload)

            import anyio as _anyio

            image_data, meta, size, ref_count = await run_codex_image_generation(
                prompt=prompt,
                references=kwargs.get("reference_images") or kwargs.get("extra_images"),
                size_hint=kwargs.get("size"),
                width=kwargs.get("width"),
                height=kwargs.get("height"),
                aspect_ratio=kwargs.get("aspect_ratio"),
                post_raw=_post,
                sleep=_anyio.sleep,
                logger=logger,
            )
            return AIResponse(
                success=True,
                data={
                    "images": [image_data],
                    "revised_prompt": meta.get("revised_prompt"),
                },
                provider=self.name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
                metadata={
                    "endpoint": "codex_responses",
                    "size": meta.get("size") or size,
                    "reference_images_count": ref_count,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Codex generate_image error: %s", exc, exc_info=True)
            return AIResponse(
                success=False,
                error=self.format_error(exc),
                provider=self.name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

    def _reload_auth(self) -> None:
        auth = read_codex_auth(self.auth_path)
        self._token = auth.access_token
        self._account_id = auth.account_id or ""

    def _recover_after_unauthorized(self) -> None:
        auth = read_codex_auth(self.auth_path)
        if auth.access_token != self._token:
            self._token = auth.access_token
            self._account_id = auth.account_id or ""
            return

        auth = refresh_codex_auth(self.auth_path)
        self._token = auth.access_token
        self._account_id = auth.account_id or ""

    def _headers(self) -> dict[str, str]:
        if not self._token:
            raise CodexAuthError("Codex access token is not loaded")
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "chatgpt-account-id": self._account_id or "",
            "originator": "codex_cli_rs",
        }

    async def _post(
        self, client: httpx.AsyncClient, payload: dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        return parse_codex_sse(await self._post_raw(client, payload))

    async def _post_raw(
        self, client: httpx.AsyncClient, payload: dict[str, Any]
    ) -> str:
        # Image tool calls stream for minutes; the read timeout must outlive them.
        timeout = httpx.Timeout(CODEX_IMAGE_TIMEOUT_SECONDS, connect=30.0)
        async with client.stream(
            "POST",
            self.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=timeout,
        ) as resp:
            if resp.status_code == 401:
                raise _CodexUnauthorized("401 Unauthorized")
            if resp.status_code >= 400:
                body = await resp.aread()
                detail = body[:300].decode(errors="replace")
                raise RuntimeError(
                    f"Codex endpoint returned {resp.status_code}: {detail}"
                )
            chunks: list[str] = []
            async for chunk in resp.aiter_text():
                chunks.append(chunk)
        return "".join(chunks)
