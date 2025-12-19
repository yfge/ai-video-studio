"""
OpenAI text generation module.

Contains text generation with streaming and JSON schema support.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import httpx

from app.core.logging import get_logger

from ..base import AIModelType, AIResponse, AITaskType
from .helpers import (
    add_additional_properties_false,
    is_openai_strict_schema,
    reload_openai_params,
    supports_json_object,
    supports_structured_outputs,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


async def stream_chat_completion(
    client: httpx.AsyncClient,
    base_url: str,
    payload: Dict[str, Any],
    model: str,
) -> tuple[str, Dict[str, Any], Optional[str]]:
    """Stream chat completion and collect response."""
    url = f"{base_url}/chat/completions"
    content_parts: list[str] = []
    usage: Dict[str, Any] = {}
    finish_reason: Optional[str] = None

    async with client.stream("POST", url, json=payload) as resp:
        if resp.status_code >= 400:
            detail = await resp.aread()
            raise httpx.HTTPStatusError(
                message=f"OpenAI stream status {resp.status_code} body={detail.decode(errors='ignore')}",
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

    full_content = "".join(content_parts).strip()
    return full_content, usage, finish_reason


async def generate_text(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    json_schema: Optional[Dict] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Generate text using GPT models."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, **kwargs}

        # Allow external control of streaming; default to on
        stream = bool(payload.pop("stream", True))
        payload.update(reload_openai_params(model, temperature))

        # Use OpenAI's response_format json_schema if available
        if json_schema:
            if supports_structured_outputs(model):
                raw_schema = json_schema.get("schema", json_schema)
                fixed_schema = add_additional_properties_false(raw_schema)
                if is_openai_strict_schema(fixed_schema):
                    payload["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": json_schema.get("name", "response"),
                            "schema": fixed_schema,
                            "strict": True,
                        },
                    }
                elif supports_json_object(model):
                    payload["response_format"] = {"type": "json_object"}
                else:
                    payload.pop("response_format", None)
            elif supports_json_object(model):
                payload["response_format"] = {"type": "json_object"}
            else:
                payload.pop("response_format", None)
        else:
            if kwargs.get("force_json_object") and supports_json_object(model):
                payload["response_format"] = {"type": "json_object"}
            else:
                payload.pop("response_format", None)

        # Stream first, fall back to non-stream on failure
        if stream:
            try:
                streamed_content, usage, finish_reason = await stream_chat_completion(
                    client,
                    base_url,
                    {**payload, "stream": True},
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
                    "OpenAI stream returned empty content; falling back to non-stream."
                )
            except Exception as stream_err:  # noqa: BLE001
                logger.warning(
                    "OpenAI stream failed, falling back to non-stream: %s",
                    stream_err,
                    exc_info=True,
                )

        response = await client.post(f"{base_url}/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
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

    except httpx.HTTPStatusError as e:
        detail = None
        try:
            detail = e.response.text
        except Exception:
            detail = None
        msg = format_error(e)
        if detail:
            msg = f"{msg}; body={detail}"
        logger.error(
            "OpenAI generate_text HTTP %s: %s",
            e.response.status_code,
            detail,
            exc_info=True,
        )
        return AIResponse(
            success=False,
            error=msg,
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
    except Exception as e:
        logger.error(f"OpenAI generate_text error: {e}", exc_info=True)
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
