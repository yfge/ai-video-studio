"""Codex Responses API payload and SSE helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def build_codex_payload(
    *,
    messages: list[dict[str, Any]],
    model: str,
    max_tokens: Optional[int],
    temperature: float,
) -> dict[str, Any]:
    instructions_parts: list[str] = []
    input_items: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            instructions_parts.append(content)
            continue
        content_type = "input_text" if role == "user" else "output_text"
        input_items.append(
            {
                "type": "message",
                "role": role,
                "content": [{"type": content_type, "text": content}],
            }
        )

    payload: dict[str, Any] = {
        "model": model,
        "instructions": "\n\n".join(instructions_parts) or " ",
        "input": input_items,
        "stream": True,
        "store": False,
    }
    if max_tokens is not None:
        payload["max_output_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    return payload


def parse_codex_sse(raw: str) -> tuple[str, Dict[str, Any]]:
    text_parts: list[str] = []
    usage: Dict[str, Any] = {}
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        for line in block.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                payload = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            event_type = payload.get("type", "")
            if event_type == "response.output_text.delta":
                delta = payload.get("delta")
                if isinstance(delta, str):
                    text_parts.append(delta)
            elif event_type == "response.completed":
                response = payload.get("response") or {}
                if isinstance(response, dict) and isinstance(
                    response.get("usage"), dict
                ):
                    usage = response["usage"]
    return "".join(text_parts), usage
