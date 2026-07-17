"""Payload and SSE helpers for Codex image generation."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Sequence


def build_codex_image_payload(
    *,
    prompt: str,
    model: str,
    size: str,
    reference_images: Sequence[str | Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    for reference in reference_images or []:
        if isinstance(reference, str) and reference.strip():
            content.append({"type": "input_image", "image_url": reference.strip()})
        elif isinstance(reference, dict) and reference.get("file_id"):
            content.append(
                {"type": "input_image", "file_id": str(reference["file_id"])}
            )
    tool: dict[str, Any] = {"type": "image_generation"}
    if size != "auto":
        tool["size"] = size
    return {
        "model": model,
        "instructions": (
            "Generate exactly one image with the image_generation tool, strictly "
            "following the user's prompt. Use any provided reference images to "
            "preserve character identity, costume, and environment appearance. "
            "Do not reply with text other than invoking the tool."
        ),
        "input": [{"type": "message", "role": "user", "content": content}],
        "tools": [tool],
        "stream": True,
        "store": False,
    }


def parse_codex_image_sse(raw: str) -> tuple[Optional[str], Dict[str, Any]]:
    """Extract a generated image and error metadata from the SSE stream."""
    image_data: Optional[str] = None
    meta: Dict[str, Any] = {}
    for block in raw.split("\n\n"):
        for line in block.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                payload = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            event_type = payload.get("type")
            if event_type == "error":
                error = payload.get("error") or {}
                meta.setdefault("error", error.get("message") or "unknown error")
                meta.setdefault("error_code", error.get("code"))
                continue
            if event_type != "response.output_item.done":
                continue
            item = payload.get("item") or {}
            if item.get("type") != "image_generation_call":
                continue
            result = item.get("result")
            if isinstance(result, str) and result:
                output_format = item.get("output_format") or "png"
                image_data = f"data:image/{output_format};base64,{result}"
                meta = {
                    "size": item.get("size"),
                    "output_format": output_format,
                    "revised_prompt": item.get("revised_prompt"),
                }
    return image_data, meta
