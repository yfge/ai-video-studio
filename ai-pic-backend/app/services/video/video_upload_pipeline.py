"""Video upload + post-process pipeline.

Keeps VideoGenerationService small by extracting:
- optional trim (ffmpeg) to match storyboard target duration
- OSS uploads for original/trimmed assets
"""

from __future__ import annotations

import base64
from typing import Any, Dict, Optional

from app.services.video.video_trim import (
    download_video_bytes,
    extract_video_frame_bytes,
    frame_aligned_duration,
    probe_video_duration_bytes,
    trim_video_bytes,
    video_exceeds_target_by_more_than_one_frame,
)
from app.services.video.video_upload_utils import (
    get_oss_url_or_original,
    upload_video_bytes_base64_to_oss,
    upload_video_bytes_to_oss,
    upload_video_last_frame_bytes_to_oss,
    upload_video_url_to_oss,
)


def _coerce_float(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f


async def upload_video_with_optional_trim(
    *,
    original_video_url: str | None,
    video_download_url: str | None,
    video_bytes_base64: str | None,
    video_mime_type: str | None,
    prompt: str,
    end_image_url: str,
    provider: str,
    model: str,
    fps: int,
    resolution: str,
    provider_duration_seconds: int,
    target_duration_seconds: float | None = None,
    logger: Any,
) -> Dict[str, Any]:
    """Upload provider video to OSS, optionally trimming to target duration.

    Returns a dict with `video_url`, `video_oss_upload`, plus optional fields for
    `untrimmed_video_url` / `untrimmed_video_oss_upload`.
    """
    trim_target = _coerce_float(target_duration_seconds)
    source_url = str(video_download_url or original_video_url or "")
    should_trim = bool(
        trim_target
        and provider_duration_seconds
        and trim_target > 0
        and trim_target < (provider_duration_seconds - 0.001)
    )

    untrimmed_oss_result = None
    untrimmed_video_url = None
    source_bytes = None
    input_ext = (
        ".webm"
        if isinstance(video_mime_type, str) and "webm" in video_mime_type.lower()
        else ".mp4"
    )

    if trim_target and trim_target > 0:
        try:
            source_bytes = (
                base64.b64decode(video_bytes_base64)
                if video_bytes_base64
                else await download_video_bytes(source_url)
            )
            actual_source_duration = probe_video_duration_bytes(
                source_bytes,
                input_ext=input_ext,
            )
            if actual_source_duration is not None:
                should_trim = video_exceeds_target_by_more_than_one_frame(
                    actual_source_duration,
                    float(trim_target),
                    fps,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Video duration probe failed, fallback: %s", exc)

    if should_trim:
        try:
            if source_bytes is None:
                source_bytes = (
                    base64.b64decode(video_bytes_base64)
                    if video_bytes_base64
                    else await download_video_bytes(source_url)
                )

            untrimmed_oss_result = await upload_video_bytes_to_oss(
                video_bytes=source_bytes,
                video_mime_type=video_mime_type,
                prompt=prompt,
                duration=provider_duration_seconds,
                fps=fps,
                resolution=resolution,
                end_image_url=end_image_url,
                provider=provider,
                model=model,
                logger=logger,
            )
            untrimmed_video_url = get_oss_url_or_original(
                untrimmed_oss_result, original_video_url
            )

            trimmed_bytes = trim_video_bytes(
                video_bytes=source_bytes,
                target_seconds=float(trim_target),
                target_fps=fps,
                input_ext=input_ext,
            )
            trimmed_frame_count, actual_trim_duration = frame_aligned_duration(
                float(trim_target), fps
            )
            trimmed_last_frame_oss_result = None
            if trimmed_frame_count:
                try:
                    last_frame_bytes = extract_video_frame_bytes(
                        video_bytes=trimmed_bytes,
                        frame_index=trimmed_frame_count - 1,
                    )
                    trimmed_last_frame_oss_result = (
                        await upload_video_last_frame_bytes_to_oss(
                            image_bytes=last_frame_bytes,
                            provider=provider,
                            logger=logger,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Trimmed last frame extraction failed: %s", exc)
            trimmed_oss_result = await upload_video_bytes_to_oss(
                video_bytes=trimmed_bytes,
                video_mime_type=video_mime_type,
                prompt=prompt,
                duration=int(round(float(trim_target))),
                fps=fps,
                resolution=resolution,
                end_image_url=end_image_url,
                provider=provider,
                model=model,
                logger=logger,
            )
            video_url = get_oss_url_or_original(trimmed_oss_result, original_video_url)
            if not video_url and untrimmed_video_url:
                video_url = untrimmed_video_url
            return {
                "video_url": video_url,
                "video_oss_upload": trimmed_oss_result,
                "untrimmed_video_url": untrimmed_video_url,
                "untrimmed_video_oss_upload": untrimmed_oss_result,
                "duration": round(float(trim_target), 3),
                "actual_trim_duration_seconds": round(actual_trim_duration, 6),
                "trimmed_video_frame_count": trimmed_frame_count,
                "trimmed_last_frame_oss_upload": trimmed_last_frame_oss_result,
                "provider_duration_seconds": provider_duration_seconds,
                "target_duration_seconds": round(float(trim_target), 3),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Video trim pipeline failed, fallback: %s", exc)

    if video_bytes_base64:
        video_oss_result = await upload_video_bytes_base64_to_oss(
            video_bytes_base64=video_bytes_base64,
            video_mime_type=video_mime_type,
            prompt=prompt,
            duration=provider_duration_seconds,
            fps=fps,
            resolution=resolution,
            end_image_url=end_image_url,
            provider=provider,
            model=model,
            logger=logger,
        )
    else:
        video_oss_result = await upload_video_url_to_oss(
            video_url=source_url,
            prompt=prompt,
            duration=provider_duration_seconds,
            fps=fps,
            resolution=resolution,
            end_image_url=end_image_url,
            provider=provider,
            model=model,
            logger=logger,
        )

    return {
        "video_url": get_oss_url_or_original(video_oss_result, original_video_url),
        "video_oss_upload": video_oss_result,
        "untrimmed_video_url": None,
        "untrimmed_video_oss_upload": None,
        "duration": provider_duration_seconds,
        "provider_duration_seconds": provider_duration_seconds,
        "target_duration_seconds": (
            None if trim_target is None else round(float(trim_target), 3)
        ),
    }
