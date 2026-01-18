"""
Google provider utility functions.

Contains helpers for model ID cleaning, image parsing, and image fetching.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx


def maybe_compress_inline_image(
    raw: bytes,
    *,
    content_type: str,
    target_max_bytes: int = 220_000,
    max_side: int = 512,
) -> Tuple[bytes, str]:
    """Downscale + re-encode reference images for inline/base64 transport."""
    if not raw or len(raw) <= target_max_bytes:
        return raw, (content_type or "image/png").split(";", 1)[0].strip()

    try:
        from io import BytesIO

        from PIL import Image, ImageOps

        img = Image.open(BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        width, height = img.size
        max_current = max(width, height) if width and height else 0
        if max_current and max_current > max_side:
            scale = max_side / float(max_current)
            new_w = max(1, int(round(width * scale)))
            new_h = max(1, int(round(height * scale)))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        for quality in (85, 75, 65):
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            out = buf.getvalue()
            if out and len(out) <= target_max_bytes:
                return out, "image/jpeg"

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60, optimize=True)
        out = buf.getvalue()
        if out:
            return out, "image/jpeg"
    except Exception:
        pass

    return raw, (content_type or "image/png").split(";", 1)[0].strip()


def clean_model_id(model: Optional[str]) -> Optional[str]:
    """Clean model ID, removing possible provider prefix (e.g., 'google:')."""
    if not model:
        return None
    # Remove provider prefix (e.g., "google:gemini-3-pro-image-preview" -> "gemini-3-pro-image-preview")
    if ":" in model:
        return model.split(":", 1)[1]
    return model


def parse_images(payload: Dict[str, Any]) -> List[str]:
    """Extract inlineData images from generateContent response as data:image/...;base64,..."""
    images: List[str] = []
    for cand in payload.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        content = cand.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if not isinstance(inline, dict):
                continue
            data = inline.get("data")
            if not data:
                continue
            mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            prefix = f"data:{mime};base64,"
            if data.startswith(prefix):
                images.append(data)
            else:
                images.append(prefix + data)
    return images


def normalize_response_modalities(raw: Any) -> List[str]:
    """Normalize response modalities for Gemini image generation."""
    default = ["TEXT", "IMAGE"]
    if not raw:
        return default
    if isinstance(raw, str):
        items: Iterable[Any] = [raw]
    elif isinstance(raw, (list, tuple, set)):
        items = raw
    else:
        return default
    normalized: List[str] = []
    for item in items:
        value = str(item).strip().upper()
        if value in {"TEXT", "IMAGE"} and value not in normalized:
            normalized.append(value)
    return normalized or default


def prefer_http_for_download(url: str) -> str:
    """Prefer HTTP for downloading reference images to avoid HTTPS cert issues."""
    if isinstance(url, str) and url.lower().startswith("https://"):
        return "http://" + url[len("https://") :]
    return url


def split_data_url(data_url: str) -> Tuple[str, str]:
    """Split data URL into mime type and base64 payload."""
    mime_type = "image/png"
    b64_data = data_url
    if isinstance(data_url, str) and data_url.startswith("data:"):
        try:
            header, b64_data = data_url.split(",", 1)
            header = header[5:]  # Remove "data:"
            if ";" in header:
                mime_type = header.split(";", 1)[0] or mime_type
            elif header:
                mime_type = header
        except ValueError:
            b64_data = data_url
    return mime_type, b64_data


def inline_part_from_data_url(data_url: str) -> Optional[Dict[str, Any]]:
    """Convert data URL or base64 string into inlineData part."""
    if not isinstance(data_url, str) or not data_url:
        return None
    mime_type, b64_data = split_data_url(data_url)
    return {"inlineData": {"mimeType": mime_type, "data": b64_data}}


def inline_parts_from_data_urls(data_urls: Sequence[str]) -> List[Dict[str, Any]]:
    """Build inlineData parts from data URLs/base64 strings."""
    parts: List[Dict[str, Any]] = []
    for data_url in list(data_urls)[:14]:
        part = inline_part_from_data_url(data_url)
        if part:
            parts.append(part)
    return parts


async def inline_parts_from_urls(
    image_urls: Sequence[str],
    timeout: Any,
) -> List[Dict[str, Any]]:
    """Fetch image URLs and build inlineData parts."""
    parts: List[Dict[str, Any]] = []
    for url in list(image_urls)[:14]:
        if not isinstance(url, str) or not url:
            continue
        if url.startswith("data:"):
            part = inline_part_from_data_url(url)
            if part:
                parts.append(part)
            continue
        inline_image = await fetch_inline_image(url, timeout)
        parts.append({"inlineData": inline_image})
    return parts


def image_bytes_from_data_url(data_url: str) -> Optional[Dict[str, str]]:
    """Convert data URL to Veo image input payload."""
    if not isinstance(data_url, str) or not data_url:
        return None
    mime_type, b64_data = split_data_url(data_url)
    return {"mimeType": mime_type, "imageBytes": b64_data}


async def fetch_image_bytes(image_url: str, timeout: Any) -> Dict[str, str]:
    """Download image and return Veo-compatible image bytes payload."""
    if isinstance(image_url, str) and image_url.startswith("data:"):
        result = image_bytes_from_data_url(image_url)
        if result:
            return result
    inline = await fetch_inline_image(image_url, timeout)
    return {"mimeType": inline.get("mimeType", "image/png"), "imageBytes": inline["data"]}


async def fetch_inline_image(image_url: str, timeout: Any) -> Dict[str, str]:
    """Download reference image and convert to inlineData structure."""
    async with httpx.AsyncClient(
        timeout=timeout,
        trust_env=False,
        follow_redirects=True,
    ) as client:
        download_url = prefer_http_for_download(image_url)
        resp = await client.get(download_url)
        resp.raise_for_status()
        mime = resp.headers.get("Content-Type", "image/png")
        content, mime = maybe_compress_inline_image(
            resp.content,
            content_type=mime,
        )
        b64 = base64.b64encode(content).decode("ascii")
        return {"mimeType": mime, "data": b64}
