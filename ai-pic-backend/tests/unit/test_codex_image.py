"""Unit tests for Codex image generation helpers."""

from __future__ import annotations

import json
from base64 import b64encode
from io import BytesIO

import pytest
from app.services.providers.codex_image import (
    build_codex_image_payload,
    parse_codex_image_sse,
    resolve_image_size,
    run_codex_image_generation,
)
from PIL import Image


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
        reference_images=[
            "https://example.com/a.png",
            " ",
            "https://example.com/b.png",
        ],
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


def _png_b64(width: int, height: int) -> str:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return b64encode(buffer.getvalue()).decode("ascii")


@pytest.mark.asyncio
async def test_codex_image_retries_wrong_physical_aspect_ratio():
    responses = [
        _sse(
            [
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "image_generation_call",
                        "result": _png_b64(1536, 1024),
                        "output_format": "png",
                    },
                }
            ]
        ),
        _sse(
            [
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "image_generation_call",
                        "result": _png_b64(900, 1600),
                        "output_format": "png",
                    },
                }
            ]
        ),
    ]
    payloads = []

    async def post_raw(payload):
        payloads.append(payload)
        return responses.pop(0)

    async def no_sleep(_seconds):
        return None

    class Logger:
        def info(self, *_args):
            pass

        def warning(self, *_args):
            pass

    image, meta, size, _ = await run_codex_image_generation(
        prompt="portrait",
        references=[],
        size_hint="auto",
        width=1024,
        height=1024,
        aspect_ratio="9:16",
        post_raw=post_raw,
        sleep=no_sleep,
        logger=Logger(),
    )

    assert len(payloads) == 2
    assert size == "1024x1536"
    assert "VERTICAL PORTRAIT" in payloads[0]["input"][0]["content"][0]["text"]
    assert image.startswith("data:image/png;base64,")
    assert (meta["actual_width"], meta["actual_height"]) == (900, 1600)


@pytest.mark.asyncio
async def test_codex_image_retries_transient_reference_download_timeout():
    calls = 0
    sleeps = []

    async def post_raw(_payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError(
                "Codex endpoint returned 400: Unable to download content from "
                "the provided URL before the timeout"
            )
        return _sse(
            [
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "image_generation_call",
                        "result": _png_b64(1024, 1024),
                        "output_format": "png",
                    },
                }
            ]
        )

    async def record_sleep(seconds):
        sleeps.append(seconds)

    class Logger:
        def info(self, *_args):
            pass

        def warning(self, *_args):
            pass

    image, _meta, _size, _refs = await run_codex_image_generation(
        prompt="storyboard",
        references=["https://example.com/reference.png"],
        size_hint="1024x1024",
        width=1024,
        height=1024,
        aspect_ratio="1:1",
        post_raw=post_raw,
        sleep=record_sleep,
        logger=Logger(),
    )

    assert calls == 2
    assert sleeps == [10]
    assert image.startswith("data:image/png;base64,")
