"""
Google text generation module.

Contains text generation with streaming support.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.core.logging import get_logger

from ..base import AIModelType, AIResponse, AITaskType

logger = get_logger(__name__)


async def stream_generate_content(
    client: httpx.AsyncClient,
    endpoint: str,
    body: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    """Stream Gemini content and collect text."""
    text_parts: List[str] = []
    usage: Dict[str, Any] = {}

    async with client.stream("POST", endpoint, json=body) as resp:
        if resp.status_code >= 400:
            detail = await resp.aread()
            raise httpx.HTTPStatusError(
                message=f"Google stream status {resp.status_code} body={detail.decode(errors='ignore')}",
                request=resp.request,
                response=resp,
            )

        async for line in resp.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except Exception:
                continue
            for candidate in event.get("candidates", []):
                content = candidate.get("content") or {}
                for part in content.get("parts", []):
                    t = part.get("text")
                    if isinstance(t, str):
                        text_parts.append(t)
            if event.get("usageMetadata"):
                usage = event["usageMetadata"]

    return "".join(text_parts).strip(), usage


async def generate_text(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    default_model: str,
    prompt: str,
    model: str | None = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    system_prompt: str | None = None,
    json_schema: Dict[str, Any] | None = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate text using Gemini models."""
    if not api_key:
        return AIResponse(
            success=False,
            error="Google API key 未配置",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    if client is None:
        return AIResponse(
            success=False,
            error="Google 客户端未初始化",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    model_id = model or default_model
    stream = bool(kwargs.pop("stream", True))
    method = "streamGenerateContent" if stream else "generateContent"
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model_id}:{method}"
    if stream:
        endpoint = f"{endpoint}?alt=sse"

    # Build request body
    contents: List[Dict[str, Any]] = [
        {
            "role": "user",
            "parts": [{"text": prompt}],
        }
    ]
    if system_prompt:
        contents.insert(
            0,
            {
                "role": "system",
                "parts": [{"text": system_prompt}],
            },
        )

    generation_config: Dict[str, Any] = {"temperature": temperature}
    if max_tokens is not None:
        generation_config["maxOutputTokens"] = max_tokens

    if json_schema:
        generation_config["responseMimeType"] = "application/json"

    body: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": generation_config,
    }

    try:
        if stream:
            try:
                full_text, usage_meta = await stream_generate_content(
                    client, endpoint, body
                )
                if full_text:
                    return AIResponse(
                        success=True,
                        data=full_text,
                        provider=provider_name,
                        model=model_id,
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION,
                        usage={
                            "prompt_tokens": (
                                usage_meta.get("promptTokenCount")
                                if usage_meta
                                else None
                            ),
                            "completion_tokens": (
                                usage_meta.get("candidatesTokenCount")
                                if usage_meta
                                else None
                            ),
                            "total_tokens": (
                                usage_meta.get("totalTokenCount")
                                if usage_meta
                                else None
                            ),
                        },
                        metadata={"raw": usage_meta, "stream": True},
                    )
                logger.warning(
                    "Google stream returned empty content; falling back to non-stream."
                )
            except Exception as stream_err:  # noqa: BLE001
                logger.warning(
                    "Google stream failed, falling back to non-stream: %s",
                    stream_err,
                    exc_info=True,
                )

        resp = await client.post(
            endpoint.replace("&alt=sse", "") if stream else endpoint, json=body
        )
        resp.raise_for_status()
        data = resp.json()

        # Parse candidates[0].content.parts[*].text
        text_parts: List[str] = []
        for candidate in data.get("candidates", []):
            content = candidate.get("content") or {}
            for part in content.get("parts", []):
                t = part.get("text")
                if isinstance(t, str):
                    text_parts.append(t)
        full_text = "\n".join(text_parts).strip()

        if not full_text:
            return AIResponse(
                success=False,
                error="Gemini 返回为空",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        usage = data.get("usageMetadata", {})

        return AIResponse(
            success=True,
            data=full_text,
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
            usage={
                "prompt_tokens": usage.get("promptTokenCount"),
                "completion_tokens": usage.get("candidatesTokenCount"),
                "total_tokens": usage.get("totalTokenCount"),
            },
            metadata={"raw": data},
        )
    except Exception as e:  # noqa: BLE001
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
