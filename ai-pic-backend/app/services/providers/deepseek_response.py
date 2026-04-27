"""Parse DeepSeek chat completion responses."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


async def collect_stream_response(
    response: httpx.Response,
) -> tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Collect content and metadata from a DeepSeek SSE response."""
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    usage: Dict[str, Any] = {}
    finish_reason: Optional[str] = None

    async for line in response.aiter_lines():
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
            reasoning_piece = delta.get("reasoning_content")
            if piece:
                content_parts.append(piece)
            if reasoning_piece:
                reasoning_parts.append(reasoning_piece)
            finish_reason = choice.get("finish_reason") or finish_reason

    return (
        "".join(content_parts).strip(),
        usage,
        finish_reason,
        "".join(reasoning_parts).strip() or None,
    )


def extract_content(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    return content.strip() if isinstance(content, str) else str(content)


def response_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    choices = data.get("choices") or []
    first_choice = choices[0] if choices else {}
    message = first_choice.get("message") or {}
    usage = data.get("usage") or {}
    metadata = {
        "finish_reason": first_choice.get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }
    if message.get("reasoning_content"):
        metadata["has_reasoning_content"] = True
    return metadata
