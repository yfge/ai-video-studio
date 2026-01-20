from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Dict, Optional

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
        video_bytes = base64.b64decode(video_bytes_base64)
        ext = ".mp4"
        if isinstance(video_mime_type, str) and "webm" in video_mime_type.lower():
            ext = ".webm"
        filename = f"video{ext}"
        return await service.upload_file_content(
            file_content=video_bytes,
            filename=filename,
            file_type="video",
            prefix="ai-generated/videos",
            metadata={
                "prompt": prompt or "image_to_video",
                "duration": str(duration),
                "fps": str(fps),
                "resolution": resolution,
                "end_image_url": end_image_url or "",
                "provider": provider,
                "model": model,
                "generation_time": datetime.now().isoformat(),
            },
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
        return await service.upload_from_url(
            url=video_url,
            file_type="video",
            prefix="ai-generated/videos",
            metadata={
                "prompt": prompt or "image_to_video",
                "duration": str(duration),
                "fps": str(fps),
                "resolution": resolution,
                "end_image_url": end_image_url or "",
                "provider": provider,
                "model": model,
                "generation_time": datetime.now().isoformat(),
            },
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
        return await service.upload_from_url(
            url=thumbnail_url,
            file_type="image",
            prefix="ai-generated/thumbnails",
            metadata={
                "type": "video_thumbnail",
                "prompt": prompt or "image_to_video",
                "provider": provider,
                "generation_time": datetime.now().isoformat(),
            },
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
        return await service.upload_from_url(
            url=last_frame_url,
            file_type="image",
            prefix="ai-generated/video-last-frames",
            metadata={
                "type": "video_last_frame",
                "prompt": prompt or "image_to_video",
                "provider": provider,
                "generation_time": datetime.now().isoformat(),
            },
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
