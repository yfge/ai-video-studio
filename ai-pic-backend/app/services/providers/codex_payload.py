"""Codex Responses API payload and SSE helpers."""

from __future__ import annotations

import json
from typing import Any, Dict


def build_codex_payload(
    *,
    messages: list[dict[str, Any]],
    model: str,
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
    return payload


def parse_codex_sse(raw: str) -> tuple[str, Dict[str, Any]]:
    text_parts: list[str] = []
    final_text = ""
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
            _raise_for_failed_response(event_type, payload)
            if event_type == "response.output_text.delta":
                delta = payload.get("delta")
                if isinstance(delta, str):
                    text_parts.append(delta)
            elif event_type == "response.output_text.done":
                final_text = _longer(final_text, payload.get("text"))
            elif event_type == "response.content_part.done":
                final_text = _longer(final_text, _content_text(payload.get("part")))
            elif event_type == "response.output_item.done":
                final_text = _longer(final_text, _message_text(payload.get("item")))
            elif event_type == "response.completed":
                response = payload.get("response") or {}
                final_text = _longer(final_text, _response_text(response))
                if isinstance(response, dict) and isinstance(
                    response.get("usage"), dict
                ):
                    usage = {**response["usage"], "_finish_reason": "stop"}
    return "".join(text_parts) or final_text, usage


def _raise_for_failed_response(event_type: str, payload: dict[str, Any]) -> None:
    response = payload.get("response")
    response = response if isinstance(response, dict) else {}
    status = str(response.get("status") or "").lower()
    if event_type not in {
        "error",
        "response.cancelled",
        "response.failed",
        "response.incomplete",
    } and status not in {"cancelled", "failed", "incomplete"}:
        return
    detail = response.get("error") or response.get("incomplete_details")
    detail = detail if isinstance(detail, dict) else payload.get("error")
    detail = detail if isinstance(detail, dict) else payload
    code = detail.get("code") or detail.get("reason") or status or event_type
    message = detail.get("message") or detail.get("detail") or ""
    raise RuntimeError(
        f"Codex response {status or event_type}: code={code}"
        + (f" message={message}" if message else "")
    )


def _longer(current: str, candidate) -> str:
    return (
        candidate
        if isinstance(candidate, str) and len(candidate) > len(current)
        else current
    )


def _content_text(part) -> str:
    if not isinstance(part, dict) or part.get("type") != "output_text":
        return ""
    return str(part.get("text") or "")


def _message_text(item) -> str:
    if not isinstance(item, dict) or item.get("type") != "message":
        return ""
    return "".join(_content_text(part) for part in item.get("content") or [])


def _response_text(response) -> str:
    if not isinstance(response, dict):
        return ""
    return "".join(_message_text(item) for item in response.get("output") or [])
