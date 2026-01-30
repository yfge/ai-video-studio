"""
Volcengine text generation module.

Contains text generation and streaming chat completion functionality.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.core.logging import get_logger

from ..base import AIModelType, AIResponse, AITaskType

if TYPE_CHECKING:
    import httpx

logger = get_logger(__name__)


async def stream_chat_completion(
    client: "httpx.AsyncClient",
    base_url: str,
    payload: Dict[str, Any],
    model: str,
) -> tuple[str, Dict[str, Any], Optional[str]]:
    """Stream chat completion and collect response."""
    import httpx as httpx_module

    url = f"{base_url}/chat/completions"
    content_parts: list[str] = []
    usage: Dict[str, Any] = {}
    finish_reason: Optional[str] = None

    async with client.stream("POST", url, json=payload) as resp:
        if resp.status_code >= 400:
            detail = await resp.aread()
            raise httpx_module.HTTPStatusError(
                message=f"Volcengine stream status {resp.status_code} body={detail.decode(errors='ignore')}",
                request=resp.request,
                response=resp,
            )

        async for line in resp.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                event = json.loads(data_str)
            except Exception:
                continue
            if event.get("usage"):
                usage = event["usage"]
            for choice in event.get("choices", []):
                delta = choice.get("delta") or {}
                piece = delta.get("content")
                if piece:
                    content_parts.append(piece)
                finish_reason = choice.get("finish_reason") or finish_reason

    return "".join(content_parts).strip(), usage, finish_reason


async def generate_text(
    client: "httpx.AsyncClient",
    base_url: str,
    provider_name: str,
    prompt: str,
    model: str = "doubao-pro-4k",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.95,
    system_prompt: Optional[str] = None,
    format_error: callable = str,
    **kwargs,
) -> AIResponse:
    """Generate text using Doubao models."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs,
        }
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens

        stream = bool(request_data.pop("stream", True))

        if stream:
            try:
                streamed_content, usage, finish_reason = await stream_chat_completion(
                    client,
                    base_url,
                    {**request_data, "stream": True},
                    model,
                )
                if streamed_content:
                    return AIResponse(
                        success=True,
                        data=streamed_content,
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION,
                        usage=usage,
                        metadata={
                            "finish_reason": finish_reason,
                            "stream": True,
                        },
                    )
                logger.warning(
                    "Volcengine stream returned empty content; falling back to non-stream."
                )
            except Exception as stream_err:  # noqa: BLE001
                logger.warning(
                    "Volcengine stream failed, falling back to non-stream: %s",
                    stream_err,
                    exc_info=True,
                )

        response = await client.post(f"{base_url}/chat/completions", json=request_data)
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            return AIResponse(
                success=False,
                error=f"火山引擎API错误: {data['error'].get('message', 'Unknown error')}",
                provider=provider_name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        content = data["choices"][0]["message"]["content"]

        return AIResponse(
            success=True,
            data=content,
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
            usage=data.get("usage", {}),
            metadata={
                "finish_reason": data["choices"][0].get("finish_reason"),
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
