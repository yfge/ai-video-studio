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


def _iter_event_dicts(event: Any) -> List[Dict[str, Any]]:
    """Normalize SSE/JSON payload into a list of dict events."""
    if isinstance(event, dict):
        return [event]
    if isinstance(event, list):
        return [item for item in event if isinstance(item, dict)]
    return []


def _collect_text_and_usage(payload: Any) -> tuple[str, Dict[str, Any]]:
    """Collect candidate text and usageMetadata from Gemini response payload.

    Some proxy gateways may return a list of event-like dicts instead of a
    single object. Handle both to avoid `'list' object has no attribute 'get'`.
    """
    text_parts: List[str] = []
    usage: Dict[str, Any] = {}

    for event in _iter_event_dicts(payload):
        for candidate in event.get("candidates", []) or []:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content") or {}
            if not isinstance(content, dict):
                continue
            for part in content.get("parts", []) or []:
                if not isinstance(part, dict):
                    continue
                t = part.get("text")
                if isinstance(t, str) and t:
                    text_parts.append(t)
        if event.get("usageMetadata"):
            usage = event["usageMetadata"]

    return "\n".join(text_parts).strip(), usage


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
                raw_event = json.loads(payload)
            except Exception:
                continue
            for event in _iter_event_dicts(raw_event):
                for candidate in event.get("candidates", []) or []:
                    if not isinstance(candidate, dict):
                        continue
                    content = candidate.get("content") or {}
                    if not isinstance(content, dict):
                        continue
                    for part in content.get("parts", []) or []:
                        if not isinstance(part, dict):
                            continue
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
    base = base_url.rstrip("/")
    stream_endpoint = f"{base}/v1beta/models/{model_id}:streamGenerateContent?alt=sse"
    generate_endpoint = f"{base}/v1beta/models/{model_id}:generateContent"

    # Build request body
    contents: List[Dict[str, Any]] = [
        {
            "role": "user",
            "parts": [{"text": prompt}],
        }
    ]
    # Gemini v1beta content roles are restricted to `user` / `model`.
    # Use systemInstruction instead of injecting a `system` role content.
    system_instruction: Dict[str, Any] | None = (
        {"parts": [{"text": system_prompt}]} if system_prompt else None
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
    if system_instruction:
        body["systemInstruction"] = system_instruction

    try:
        if stream:
            try:
                full_text, usage_meta = await stream_generate_content(
                    client, stream_endpoint, body
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

        resp = await client.post(generate_endpoint, json=body)
        resp.raise_for_status()
        data = resp.json()
        full_text, usage_meta = _collect_text_and_usage(data)

        if not full_text:
            return AIResponse(
                success=False,
                error="Gemini 返回为空",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        return AIResponse(
            success=True,
            data=full_text,
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
            usage={
                "prompt_tokens": (usage_meta or {}).get("promptTokenCount"),
                "completion_tokens": (usage_meta or {}).get("candidatesTokenCount"),
                "total_tokens": (usage_meta or {}).get("totalTokenCount"),
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
