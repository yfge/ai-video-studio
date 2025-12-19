"""
Google provider utility functions.

Contains helpers for model ID cleaning, image parsing, and image fetching.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

import httpx


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


def prefer_http_for_download(url: str) -> str:
    """Prefer HTTP for downloading reference images to avoid HTTPS cert issues."""
    if isinstance(url, str) and url.lower().startswith("https://"):
        return "http://" + url[len("https://") :]
    return url


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
        b64 = base64.b64encode(resp.content).decode("ascii")
        return {"mimeType": mime, "data": b64}
