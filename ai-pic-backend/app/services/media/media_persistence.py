"""
Media persistence helpers.

Centralizes upload to OSS/CDN for image/video/audio so generation pipelines can
reuse a single entrypoint and metadata contract.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from app.services.storage import oss_service
from app.utils.url_utils import normalize_presigned_url

MediaType = Literal["image", "video", "audio"]

DEFAULT_PREFIX_BY_MEDIA_TYPE: dict[MediaType, str] = {
    "image": "ai-generated/images",
    "video": "ai-generated/videos",
    "audio": "ai-generated/audio",
}


def _filter_ascii_metadata(metadata: dict[str, Any] | None) -> dict[str, str]:
    if not metadata:
        return {}
    safe: dict[str, str] = {}
    for key, value in metadata.items():
        try:
            key_str = str(key)
            value_str = str(value)
            key_str.encode("ascii")
            value_str.encode("ascii")
        except Exception:  # noqa: BLE001 - defensive: avoid breaking uploads on metadata issues
            continue
        safe[key_str] = value_str
    return safe


def build_generation_metadata(
    *,
    provider: str,
    model: str | None,
    media_type: MediaType,
    mime_type: str | None = None,
    duration_seconds: int | None = None,
    fps: int | None = None,
    resolution: str | None = None,
    sha256: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, str]:
    base: dict[str, Any] = {
        "media_type": media_type,
        "provider": provider,
        "model": model or "",
        "mime_type": mime_type or "",
        "duration_seconds": "" if duration_seconds is None else int(duration_seconds),
        "fps": "" if fps is None else int(fps),
        "resolution": resolution or "",
        "sha256": sha256 or "",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if extra:
        base.update(extra)
    return _filter_ascii_metadata(base)


async def upload_from_url(
    *,
    url: str,
    media_type: MediaType,
    prefix: str | None = None,
    metadata: dict[str, Any] | None = None,
    oss_service_override: Any | None = None,
) -> Optional[dict[str, Any]]:
    service = oss_service_override or oss_service
    if not url or not service:
        return None

    normalized = normalize_presigned_url(url)
    return await service.upload_from_url(
        url=normalized,
        file_type=media_type,
        prefix=prefix or DEFAULT_PREFIX_BY_MEDIA_TYPE[media_type],
        metadata=_filter_ascii_metadata(metadata),
    )


async def upload_bytes(
    *,
    content: bytes,
    filename: str,
    media_type: MediaType,
    prefix: str | None = None,
    metadata: dict[str, Any] | None = None,
    oss_service_override: Any | None = None,
) -> Optional[dict[str, Any]]:
    service = oss_service_override or oss_service
    if not content or not filename or not service:
        return None

    return await service.upload_file_content(
        file_content=content,
        filename=filename,
        file_type=media_type,
        prefix=prefix or DEFAULT_PREFIX_BY_MEDIA_TYPE[media_type],
        metadata=_filter_ascii_metadata(metadata),
    )


async def upload_base64(
    *,
    base64_payload: str,
    filename: str,
    media_type: MediaType,
    prefix: str | None = None,
    metadata: dict[str, Any] | None = None,
    oss_service_override: Any | None = None,
) -> Optional[dict[str, Any]]:
    if not base64_payload:
        return None
    content = base64.b64decode(base64_payload)
    sha256 = hashlib.sha256(content).hexdigest()
    merged = dict(metadata or {})
    merged.setdefault("sha256", sha256)
    return await upload_bytes(
        content=content,
        filename=filename,
        media_type=media_type,
        prefix=prefix,
        metadata=merged,
        oss_service_override=oss_service_override,
    )
