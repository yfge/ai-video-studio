"""Prepare local image inputs for Volcengine video requests."""

from __future__ import annotations

import base64
import binascii
import io
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.core.config import settings
from PIL import Image

LOCAL_VIDEO_IMAGE_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "ai-video-backend",
}
MAX_SINGLE_IMAGE_BYTES = 30 * 1024 * 1024
# Base64 expands raw bytes by roughly 4/3. Keep the encoded JSON body below
# Volcengine's 64 MiB request limit with room for prompts and field overhead.
MAX_TOTAL_INLINE_IMAGE_BYTES = 45 * 1024 * 1024


class VideoImageInputError(ValueError):
    """Raised before a provider call when a required image cannot be prepared."""


def prepare_video_image_inputs(
    *,
    image_url: str | None,
    end_image_url: str | None,
    reference_images: list[str],
    reference_field: str,
) -> tuple[str | None, str | None, list[str]]:
    """Inline local uploads while preserving provider-reachable references."""
    inline_bytes = [0]
    prepared_image = _prepare_required(image_url, "image_url", inline_bytes)
    prepared_end = _prepare_required(
        end_image_url,
        "end_image_url",
        inline_bytes,
    )
    prepared_refs = [
        _prepare_image(
            reference,
            f"{reference_field}[{index}]",
            inline_bytes,
        )
        for index, reference in enumerate(reference_images, start=1)
    ]
    return prepared_image, prepared_end, prepared_refs


def _prepare_required(
    value: str | None,
    label: str,
    inline_bytes: list[int],
) -> str | None:
    if value is None:
        return None
    return _prepare_image(value, label, inline_bytes)


def _prepare_image(value: str, label: str, inline_bytes: list[int]) -> str:
    source = value.strip()
    if not source:
        raise VideoImageInputError(f"Volcengine {label} is empty")
    if source.lower().startswith("data:image/"):
        _reserve_data_url(source, label, inline_bytes)
        return source
    local_path = _local_upload_path(source, label)
    if local_path is None:
        return source
    content = _read_local_image(local_path, source, label, inline_bytes)
    mime = _sniff_image_mime(content, source, label)
    inline_bytes[0] += len(content)
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _local_upload_path(source: str, label: str) -> Path | None:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        if not _is_local_video_image_host(parsed.hostname):
            return None
        path = unquote(parsed.path)
        if not path.startswith("/uploads/"):
            raise VideoImageInputError(
                f"Volcengine {label} local URL must point under /uploads: {source}"
            )
    elif parsed.scheme:
        return None
    else:
        path = unquote(parsed.path)
        if not path.startswith(("/uploads/", "uploads/")):
            return None

    relative_path = path.lstrip("/")[len("uploads/") :]
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    candidate = (upload_root / relative_path).resolve()
    if not relative_path or upload_root not in candidate.parents:
        raise VideoImageInputError(
            f"Volcengine {label} has an invalid local upload path: {source}"
        )
    return candidate


def _read_local_image(
    path: Path,
    source: str,
    label: str,
    inline_bytes: list[int],
) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise VideoImageInputError(
            f"Volcengine {label} local image cannot be read: {source} ({exc})"
        ) from exc
    _validate_size(size, label, inline_bytes[0])
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise VideoImageInputError(
            f"Volcengine {label} local image cannot be read: {source} ({exc})"
        ) from exc
    _validate_size(len(content), label, inline_bytes[0])
    return content


def _reserve_data_url(source: str, label: str, inline_bytes: list[int]) -> None:
    try:
        header, encoded = source.split(",", 1)
        if ";base64" not in header.lower():
            raise ValueError("not base64 encoded")
        estimated_size = max((len(encoded.rstrip("=")) * 3) // 4, 0)
        _validate_size(estimated_size, label, inline_bytes[0])
        decoded = base64.b64decode(encoded, validate=True)
    except VideoImageInputError:
        raise
    except (ValueError, binascii.Error) as exc:
        raise VideoImageInputError(
            f"Volcengine {label} contains an invalid image data URL"
        ) from exc
    decoded_size = len(decoded)
    _validate_size(decoded_size, label, inline_bytes[0])
    _sniff_image_mime(decoded, "data URL", label)
    inline_bytes[0] += decoded_size


def _is_local_video_image_host(hostname: str | None) -> bool:
    normalized = (hostname or "").lower()
    configured = urlparse(getattr(settings, "INTERNAL_BACKEND_URL", None) or "")
    configured_host = (configured.hostname or "").lower()
    return normalized in LOCAL_VIDEO_IMAGE_HOSTS or bool(
        configured_host and normalized == configured_host
    )


def _validate_size(size: int, label: str, current_total: int) -> None:
    if size >= MAX_SINGLE_IMAGE_BYTES:
        raise VideoImageInputError(
            f"Volcengine {label} image must be smaller than "
            f"{MAX_SINGLE_IMAGE_BYTES} bytes"
        )
    if current_total + size >= MAX_TOTAL_INLINE_IMAGE_BYTES:
        raise VideoImageInputError(
            "Volcengine inline image total must be smaller than "
            f"{MAX_TOTAL_INLINE_IMAGE_BYTES} bytes"
        )


def _sniff_image_mime(content: bytes, source: str, label: str) -> str:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image_format = image.format
            image.verify()
    except Exception as exc:
        raise VideoImageInputError(
            f"Volcengine {label} is not a valid image: {source}"
        ) from exc
    mime = Image.MIME.get(image_format or "")
    if not mime or not mime.startswith("image/"):
        raise VideoImageInputError(
            f"Volcengine {label} image format is unsupported: {source}"
        )
    return mime
