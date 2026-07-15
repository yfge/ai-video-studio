"""Image generation via the ChatGPT Codex responses endpoint.

Uses the Responses API `image_generation` tool with the Codex OAuth token, so
image output is billed to the ChatGPT subscription instead of an API key.
"""

from __future__ import annotations

import base64
import io
import json
from typing import Any, Dict, List, Optional, Sequence

import httpx

from .codex_image_aspect import (
    image_matches_aspect_ratio,
    prompt_with_aspect_contract,
    resolve_image_size,
)

DEFAULT_IMAGE_TOOL_MODEL = "gpt-5.4"
REFERENCE_MAX_EDGE = 1024
REFERENCE_FETCH_TIMEOUT = 20.0
MAX_REFERENCE_IMAGES = 6


INTERNAL_HOST_MARKERS = ("localhost", "127.0.0.1", "ai-video-backend")


def _is_public_url(url: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith(("http://", "https://")):
        return False
    return not any(marker in lowered for marker in INTERNAL_HOST_MARKERS)


async def inline_reference_images(urls: Sequence[str] | None) -> List[str]:
    """Normalize reference images for the ChatGPT image tool.

    Publicly reachable URLs are passed through untouched (the endpoint
    downloads them itself; inlined base64 payloads have proven flaky).
    Intranet URLs (backend uploads) are downloaded and inlined as downscaled
    data URLs as a best effort; unreachable references are skipped instead of
    failing the whole generation.
    """
    prepared: List[str] = []
    pending_internal: List[str] = []
    if not urls:
        return prepared
    for url in list(urls)[:MAX_REFERENCE_IMAGES]:
        if not isinstance(url, str) or not url.strip():
            continue
        url = url.strip()
        if url.startswith("data:"):
            prepared.append(url)
        elif _is_public_url(url):
            prepared.append(url)
        else:
            pending_internal.append(url)
    if pending_internal:
        async with httpx.AsyncClient(timeout=REFERENCE_FETCH_TIMEOUT) as client:
            for url in pending_internal:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    resp.raise_for_status()
                    prepared.append(_downscale_to_data_url(resp.content))
                except Exception:  # noqa: BLE001
                    continue
    return prepared


def _downscale_to_data_url(content: bytes) -> str:
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(content))
        image.load()
        if max(image.size) > REFERENCE_MAX_EDGE:
            image.thumbnail((REFERENCE_MAX_EDGE, REFERENCE_MAX_EDGE))
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=88)
        payload = buffer.getvalue()
        mime = "image/jpeg"
    except Exception:  # noqa: BLE001
        payload = content
        mime = "image/png"
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def build_codex_image_payload(
    *,
    prompt: str,
    model: str,
    size: str,
    reference_images: Sequence[str] | None = None,
) -> Dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    for url in reference_images or []:
        if isinstance(url, str) and url.strip():
            content.append({"type": "input_image", "image_url": url.strip()})
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


async def run_codex_image_generation(
    *,
    prompt: str,
    references: Sequence[str] | None,
    size_hint: Optional[str],
    width: Optional[int],
    height: Optional[int],
    aspect_ratio: Optional[str],
    post_raw,
    sleep,
    logger,
) -> tuple[str, Dict[str, Any], str, int]:
    """Run the image tool call with inlined references and one delayed retry.

    Returns (image_data_url, meta, size, reference_count); raises on failure.
    """
    if isinstance(references, str):
        references = [references]
    inlined = await inline_reference_images(references)
    size = resolve_image_size(size_hint, width, height, aspect_ratio)
    logger.info(
        "Codex image canvas resolved | aspect_ratio=%s size=%s width=%s height=%s refs=%s",
        aspect_ratio,
        size,
        width,
        height,
        len(inlined),
    )
    payload = build_codex_image_payload(
        prompt=prompt_with_aspect_contract(prompt, aspect_ratio),
        model=DEFAULT_IMAGE_TOOL_MODEL,
        size=size,
        reference_images=inlined,
    )
    image_data: Optional[str] = None
    meta: Dict[str, Any] = {}
    # The ChatGPT image tool intermittently returns server_error; one delayed
    # retry recovers transient failures (sustained ones are rate limiting).
    for attempt in range(2):
        try:
            raw = await post_raw(payload)
        except Exception as exc:
            if attempt == 0 and _is_transient_reference_fetch_error(exc):
                meta = {"error": str(exc)}
                logger.warning(
                    "Codex reference download timed out; retrying once: %s",
                    exc,
                )
                await sleep(10)
                continue
            raise
        candidate, meta = parse_codex_image_sse(raw)
        if candidate:
            matches, dimensions = image_matches_aspect_ratio(candidate, aspect_ratio)
            if dimensions:
                meta["actual_width"], meta["actual_height"] = dimensions
            if matches:
                image_data = candidate
                break
            meta["error"] = (
                "Codex image physical aspect ratio mismatch: "
                f"expected={aspect_ratio}, actual={dimensions}"
            )
        logger.warning(
            "Codex image_generation failed (attempt %s): %s",
            attempt + 1,
            meta.get("error"),
        )
        if attempt == 0:
            await sleep(10)
    if not image_data:
        raise RuntimeError(
            meta.get("error") or "Codex image_generation returned no image result"
        )
    return image_data, meta, size, len(inlined)


def _is_transient_reference_fetch_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "unable to download content" in message and "provided url" in message


def parse_codex_image_sse(raw: str) -> tuple[Optional[str], Dict[str, Any]]:
    """Extract the generated image (data URL) and metadata from the SSE stream.

    On failure the metadata carries ``error``/``error_code`` from the stream's
    error events so callers can surface and retry on server errors.
    """
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
