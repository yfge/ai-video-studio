"""Unit tests for Codex image generation helpers."""

from __future__ import annotations

import json

from app.services.providers.codex_image import (
    build_codex_image_payload,
    parse_codex_image_sse,
    resolve_image_size,
)


def test_resolve_image_size_maps_aspect_ratios():
    assert resolve_image_size(None, None, None, "16:9") == "1536x1024"
    assert resolve_image_size(None, None, None, "9:16") == "1024x1536"
    assert resolve_image_size(None, None, None, "1:1") == "1024x1024"
    assert resolve_image_size("1536x1024", None, None, None) == "1536x1024"
    assert resolve_image_size(None, 1920, 1080, None) == "1536x1024"
    assert resolve_image_size(None, None, None, None) == "auto"


def test_payload_includes_references_and_size():
    payload = build_codex_image_payload(
        prompt="a grid storyboard",
        model="gpt-5.4",
        size="1536x1024",
        reference_images=["https://example.com/a.png", " ", "https://example.com/b.png"],
    )
    content = payload["input"][0]["content"]
    assert content[0] == {"type": "input_text", "text": "a grid storyboard"}
    image_urls = [c["image_url"] for c in content if c["type"] == "input_image"]
    assert image_urls == ["https://example.com/a.png", "https://example.com/b.png"]
    assert payload["tools"] == [{"type": "image_generation", "size": "1536x1024"}]


def test_payload_auto_size_omits_size_param():
    payload = build_codex_image_payload(prompt="p", model="gpt-5.4", size="auto")
    assert payload["tools"] == [{"type": "image_generation"}]


def _sse(events):
    return "\n\n".join(f"data: {json.dumps(e)}" for e in events)


def test_parse_sse_extracts_image_result():
    raw = _sse(
        [
            {"type": "response.created"},
            {
                "type": "response.output_item.done",
                "item": {
                    "type": "image_generation_call",
                    "result": "QUJD",
                    "output_format": "png",
                    "size": "1536x1024",
                },
            },
        ]
    )
    image, meta = parse_codex_image_sse(raw)
    assert image == "data:image/png;base64,QUJD"
    assert meta["size"] == "1536x1024"


def test_parse_sse_surfaces_server_error():
    raw = _sse(
        [
            {
                "type": "error",
                "error": {"code": "server_error", "message": "boom"},
            },
            {"type": "response.failed"},
        ]
    )
    image, meta = parse_codex_image_sse(raw)
    assert image is None
    assert meta["error"] == "boom"
    assert meta["error_code"] == "server_error"
