"""
MiniMax text generation module.
"""

from __future__ import annotations

from typing import Callable, Optional

from app.services.minimax_client import MinimaxAPIError, MinimaxClient

from ..base import AIModelType, AIResponse, AITaskType


async def generate_text(
    client: MinimaxClient,
    provider_name: str,
    prompt: str,
    model: str = "abab6.5-chat",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.95,
    system_prompt: str = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Generate text using MiniMax models."""
    try:
        # MiniMax doesn't support streaming, ignore stream flag
        kwargs.pop("stream", None)

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

        data = await client.post_json("/text/chatcompletion_v2", request_data)
        content = data.get("choices", [{}])[0].get("message", {}).get("content")

        return AIResponse(
            success=True,
            data=content,
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
            usage=data.get("usage", {}),
            metadata={
                "finish_reason": data.get("choices", [{}])[0].get("finish_reason"),
                "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                "trace_id": data.get("trace_id"),
            },
        )
    except MinimaxAPIError as err:
        return AIResponse(
            success=False,
            error=format_error(err),
            provider=provider_name,
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )
