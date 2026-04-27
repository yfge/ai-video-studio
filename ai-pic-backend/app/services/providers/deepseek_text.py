"""DeepSeek text generation helpers."""

from __future__ import annotations

from typing import Any, Callable, Optional

import httpx

from .base import AIModelType, AIResponse, AITaskType
from .deepseek_models import DEEPSEEK_DEFAULT_MODEL
from .deepseek_request import build_chat_request
from .deepseek_response import (
    collect_stream_response,
    extract_content,
    response_metadata,
)


async def generate_text(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.95,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    system_prompt: Optional[str] = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate text using DeepSeek Chat Completions."""
    model_id, request_data, stream = build_chat_request(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        system_prompt=system_prompt,
        extra_kwargs=kwargs,
    )
    try:
        if stream:
            try:
                response = await _try_stream(
                    client,
                    base_url,
                    provider_name,
                    model_id,
                    request_data,
                )
                if response.success:
                    return response
            except Exception:
                pass

        response = await client.post(
            f"{base_url}/chat/completions",
            json=request_data,
        )
        response.raise_for_status()
        data = response.json()
        return _success_response(
            provider_name,
            model_id,
            extract_content(data),
            data.get("usage") or {},
            response_metadata(data),
        )
    except Exception as exc:
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model=model_id or DEEPSEEK_DEFAULT_MODEL,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )


async def _try_stream(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    model_id: str,
    request_data: dict,
) -> AIResponse:
    url = f"{base_url}/chat/completions"
    async with client.stream(
        "POST", url, json={**request_data, "stream": True}
    ) as resp:
        if resp.status_code >= 400:
            detail = await resp.aread()
            raise httpx.HTTPStatusError(
                message=(
                    f"DeepSeek stream status {resp.status_code} "
                    f"body={detail.decode(errors='ignore')}"
                ),
                request=resp.request,
                response=resp,
            )
        content, usage, finish_reason, reasoning = await collect_stream_response(resp)
    if not content:
        return AIResponse(
            success=False,
            error="DeepSeek stream returned empty content",
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
    metadata = {"finish_reason": finish_reason, "stream": True}
    if reasoning:
        metadata["has_reasoning_content"] = True
    return _success_response(provider_name, model_id, content, usage, metadata)


def _success_response(
    provider_name: str,
    model: str,
    content: str,
    usage: dict,
    metadata: dict,
) -> AIResponse:
    return AIResponse(
        success=True,
        data=content,
        provider=provider_name,
        model=model,
        task_type=AITaskType.STORY_GENERATION,
        model_type=AIModelType.TEXT_GENERATION,
        usage=usage,
        metadata=metadata,
    )
