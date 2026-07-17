"""Reference image preparation for the ChatGPT Codex image provider."""

from __future__ import annotations

import asyncio
import base64
import io
import time
import uuid
from typing import Sequence
from urllib.parse import urlparse, urlunparse

import httpx
from app.core.config import settings

REFERENCE_MAX_EDGE = 1024
REFERENCE_FETCH_TIMEOUT = 20.0
REFERENCE_UPLOAD_TIMEOUT = 60.0
REFERENCE_FINALIZE_TIMEOUT = 30.0
MAX_REFERENCE_IMAGES = 6

INTERNAL_HOST_MARKERS = ("localhost", "127.0.0.1", "ai-video-backend")


def clean_reference_images(urls: Sequence[str] | None) -> list[str]:
    return [
        value
        for raw in list(urls or [])[:MAX_REFERENCE_IMAGES]
        if isinstance(raw, str) and (value := raw.strip())
    ]


def _is_public_url(url: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith(("http://", "https://")):
        return False
    return not any(marker in lowered for marker in INTERNAL_HOST_MARKERS)


def _provider_reachable_url(url: str) -> str:
    """Prefer the configured OSS origin over a custom CDN domain."""
    parsed = urlparse(url)
    custom = urlparse(getattr(settings, "ALIYUN_OSS_DOMAIN", None) or "")
    endpoint = urlparse(getattr(settings, "ALIYUN_OSS_ENDPOINT", None) or "")
    bucket = getattr(settings, "ALIYUN_OSS_BUCKET", None)
    endpoint_host = endpoint.netloc or endpoint.path
    if parsed.netloc != custom.netloc or not endpoint_host or not bucket:
        return url
    return urlunparse(
        ("https", f"{bucket}.{endpoint_host}", parsed.path, "", parsed.query, "")
    )


async def inline_reference_images(urls: Sequence[str] | None) -> list[str]:
    """Keep public URLs and inline references that Codex cannot reach."""
    prepared: list[str] = []
    pending_internal: list[str] = []
    for url in clean_reference_images(urls):
        if url.startswith("data:"):
            prepared.append(url)
        elif _is_public_url(url):
            prepared.append(_provider_reachable_url(url))
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
        payload, mime = buffer.getvalue(), "image/jpeg"
    except Exception:  # noqa: BLE001
        payload, mime = content, "image/png"
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def _file_base_url(responses_url: str) -> str:
    suffix = "/codex/responses"
    clean = responses_url.rstrip("/")
    return clean[: -len(suffix)] if clean.endswith(suffix) else clean


async def _load_reference(
    client: httpx.AsyncClient, reference: str
) -> tuple[bytes, str]:
    if reference.startswith("data:"):
        header, encoded = reference.split(",", 1)
        mime = header[5:].split(";", 1)[0] or "image/png"
        return base64.b64decode(encoded), mime
    response = await client.get(
        reference, follow_redirects=True, timeout=REFERENCE_FETCH_TIMEOUT
    )
    response.raise_for_status()
    return response.content, response.headers.get("content-type", "image/png")


async def _create_file_slot(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    headers: dict[str, str],
    file_name: str,
    file_size: int,
) -> tuple[str, str]:
    response = await client.post(
        f"{base_url}/files",
        headers=headers,
        json={"file_name": file_name, "file_size": file_size, "use_case": "codex"},
        timeout=REFERENCE_UPLOAD_TIMEOUT,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Codex file slot creation failed: HTTP {response.status_code}"
        )
    payload = response.json()
    return str(payload["file_id"]), str(payload["upload_url"])


async def _put_file_blob(
    client: httpx.AsyncClient, *, upload_url: str, content: bytes
) -> None:
    response = await client.put(
        upload_url,
        headers={
            "Content-Length": str(len(content)),
            "x-ms-blob-type": "BlockBlob",
            "x-ms-client-request-id": str(uuid.uuid4()),
        },
        content=content,
        timeout=REFERENCE_UPLOAD_TIMEOUT,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Codex file blob upload failed: HTTP {response.status_code}"
        )


async def _finalize_file(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    headers: dict[str, str],
    file_id: str,
) -> None:
    deadline = time.monotonic() + REFERENCE_FINALIZE_TIMEOUT
    while True:
        response = await client.post(
            f"{base_url}/files/{file_id}/uploaded",
            headers=headers,
            json={},
            timeout=REFERENCE_UPLOAD_TIMEOUT,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Codex file finalization failed: HTTP {response.status_code}"
            )
        payload = response.json()
        if payload.get("status") == "success":
            return
        if payload.get("status") != "retry" or time.monotonic() >= deadline:
            raise RuntimeError(
                f"Codex file finalization failed: {payload.get('status') or 'timeout'}"
            )
        await asyncio.sleep(0.25)


async def upload_codex_reference_files(
    urls: Sequence[str],
    *,
    client: httpx.AsyncClient,
    responses_url: str,
    headers: dict[str, str],
) -> list[str]:
    """Upload reference images using the same file protocol as Codex CLI."""
    base_url = _file_base_url(responses_url)
    file_ids: list[str] = []
    for index, reference in enumerate(clean_reference_images(urls), start=1):
        content, content_type = await _load_reference(client, reference)
        subtype = content_type.split(";", 1)[0].split("/", 1)[-1]
        extension = "jpg" if subtype == "jpeg" else subtype or "png"
        file_id, upload_url = await _create_file_slot(
            client,
            base_url=base_url,
            headers=headers,
            file_name=f"reference-{index}.{extension}",
            file_size=len(content),
        )
        await _put_file_blob(client, upload_url=upload_url, content=content)
        await _finalize_file(
            client, base_url=base_url, headers=headers, file_id=file_id
        )
        file_ids.append(file_id)
    return file_ids
