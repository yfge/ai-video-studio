from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.media import (
    build_generation_metadata,
    upload_base64 as upload_media_base64,
    upload_from_url as upload_media_from_url,
)
from app.services.storage import oss_service


async def upload_video_bytes_base64_to_oss(
    *,
    video_bytes_base64: str,
    video_mime_type: str | None,
    prompt: str,
    duration: int,
    fps: int,
    resolution: str,
    end_image_url: str,
    provider: str,
    model: str,
    logger: Any,
    oss_service_override: Any | None = None,
) -> Optional[Dict[str, Any]]:
    service = oss_service_override or oss_service
    if not video_bytes_base64 or not service:
        return None

    try:
        ext = ".mp4"
        if isinstance(video_mime_type, str) and "webm" in video_mime_type.lower():
            ext = ".webm"
        filename = f"video{ext}"
        return await upload_media_base64(
            base64_payload=video_bytes_base64,
            filename=filename,
            media_type="video",
            prefix="ai-generated/videos",
            metadata=build_generation_metadata(
                provider=provider,
                model=model,
                media_type="video",
                mime_type=video_mime_type,
                duration_seconds=duration,
                fps=fps,
                resolution=resolution,
                extra={
                    # Keep this for debugging/tracing; may be truncated/filtered later.
                    "end_image_url": end_image_url or "",
                },
            ),
            oss_service_override=service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Video OSS upload (bytes) failed: %s", exc)
        return None


async def upload_video_url_to_oss(
    *,
    video_url: str,
    prompt: str,
    duration: int,
    fps: int,
    resolution: str,
    end_image_url: str,
    provider: str,
    model: str,
    logger: Any,
    oss_service_override: Any | None = None,
) -> Optional[Dict[str, Any]]:
    service = oss_service_override or oss_service
    if not video_url or not service:
        return None

    try:
        return await upload_media_from_url(
            url=video_url,
            media_type="video",
            prefix="ai-generated/videos",
            metadata=build_generation_metadata(
                provider=provider,
                model=model,
                media_type="video",
                duration_seconds=duration,
                fps=fps,
                resolution=resolution,
                extra={
                    "end_image_url": end_image_url or "",
                },
            ),
            oss_service_override=service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Video OSS upload failed: %s", exc)
        return None


async def upload_video_thumbnail_to_oss(
    *,
    thumbnail_url: str,
    prompt: str,
    provider: str,
    logger: Any,
    oss_service_override: Any | None = None,
) -> Optional[Dict[str, Any]]:
    service = oss_service_override or oss_service
    if not thumbnail_url or not service:
        return None

    try:
        return await upload_media_from_url(
            url=thumbnail_url,
            media_type="image",
            prefix="ai-generated/thumbnails",
            metadata=build_generation_metadata(
                provider=provider,
                model=None,
                media_type="image",
                extra={"type": "video_thumbnail"},
            ),
            oss_service_override=service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Thumbnail OSS upload failed: %s", exc)
        return None


async def upload_video_last_frame_to_oss(
    *,
    last_frame_url: str,
    prompt: str,
    provider: str,
    logger: Any,
    oss_service_override: Any | None = None,
) -> Optional[Dict[str, Any]]:
    service = oss_service_override or oss_service
    if not last_frame_url or not service:
        return None

    try:
        return await upload_media_from_url(
            url=last_frame_url,
            media_type="image",
            prefix="ai-generated/video-last-frames",
            metadata=build_generation_metadata(
                provider=provider,
                model=None,
                media_type="image",
                extra={"type": "video_last_frame"},
            ),
            oss_service_override=service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Last frame OSS upload failed: %s", exc)
        return None


def get_oss_url_or_original(
    oss_result: Optional[Dict[str, Any]],
    original_url: str,
) -> Optional[str]:
    if oss_result and oss_result.get("success"):
        return oss_result.get("file_url")
    return original_url
