from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


def _normalize_ratio(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = str(value).strip().replace("：", ":")
    if cleaned in {"9:16", "16:9"}:
        return cleaned
    return None


def _parse_dimensions(
    resolution: Optional[str], ratio: Optional[str]
) -> Tuple[Optional[int], Optional[int]]:
    """Best-effort parse width/height from common resolution representations."""
    if not resolution:
        return None, None

    res = str(resolution).strip().lower().replace("×", "x")
    if "x" in res:
        left, _, right = res.partition("x")
        try:
            return int(left), int(right)
        except ValueError:
            return None, None

    match = re.fullmatch(r"(\d{3,4})p", res)
    if match:
        p = int(match.group(1))
        ratio_norm = _normalize_ratio(ratio)
        # 720p typically means height=720 for landscape, and width=720 for portrait.
        if ratio_norm == "9:16":
            return p, int(round(p * 16 / 9))
        return int(round(p * 16 / 9)), p

    return None, None


def _extract_asset(
    oss_upload: Any,
    *,
    fallback_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(oss_upload, dict):
        if fallback_url:
            return {"url": fallback_url}
        return None

    meta = oss_upload.get("metadata")
    if not isinstance(meta, dict):
        meta = {}

    url = oss_upload.get("file_url") or fallback_url
    return {
        "url": url,
        "object_key": oss_upload.get("object_key"),
        "file_size": oss_upload.get("file_size"),
        "mime_type": oss_upload.get("content_type") or meta.get("mime_type"),
        "sha256": meta.get("sha256") or None,
    }


def build_video_generation_metadata(
    provider: str,
    model: Optional[str],
    provider_task_id: Optional[str],
    model_type: Optional[str],
    params: Optional[Dict[str, Any]] = None,
    result_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build normalized DB metadata for a single storyboard video generation task."""
    params = dict(params or {})
    result_payload = dict(result_payload or {})

    ratio = _normalize_ratio(params.get("ratio"))
    resolution = params.get("resolution")
    width, height = _parse_dimensions(str(resolution) if resolution else None, ratio)

    target_duration_seconds = params.get("target_duration_seconds")
    provider_duration_seconds = params.get("provider_duration_seconds") or params.get(
        "duration"
    )

    video_original = result_payload.get("original_video_url") or result_payload.get(
        "video_url"
    )
    thumb_original = result_payload.get("original_thumbnail_url") or result_payload.get(
        "thumbnail_url"
    )
    last_original = result_payload.get("original_last_frame_url") or result_payload.get(
        "last_frame_url"
    )

    return {
        "provider": provider,
        "model": model,
        "task_id": provider_task_id,
        "provider_task_id": provider_task_id,
        "model_type": model_type,
        "duration_seconds": result_payload.get("duration")
        or target_duration_seconds
        or provider_duration_seconds,
        "target_duration_seconds": target_duration_seconds,
        "provider_duration_seconds": provider_duration_seconds,
        "allowed_durations": params.get("allowed_durations"),
        "capability_source": params.get("capability_source"),
        "fps": params.get("fps"),
        "resolution": resolution,
        "ratio": ratio,
        "width": width,
        "height": height,
        "assets": {
            "video": _extract_asset(
                result_payload.get("video_oss_upload"),
                fallback_url=video_original,
            ),
            "thumbnail": _extract_asset(
                result_payload.get("thumbnail_oss_upload"),
                fallback_url=thumb_original,
            ),
            "last_frame": _extract_asset(
                result_payload.get("last_frame_oss_upload"),
                fallback_url=last_original,
            ),
        },
    }
