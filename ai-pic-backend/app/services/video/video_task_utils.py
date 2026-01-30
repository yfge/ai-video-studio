from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.services.providers.polling_utils import TaskStatus as ProviderTaskStatus


def abs_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http"):
        parsed = url.split("//", 1)[-1]
        host = parsed.split("/", 1)[0].split(":")[0]
        if host in {"localhost", "127.0.0.1"}:
            base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")
            return f"{base}/{parsed.split('/', 1)[1]}"
        return url
    if not url.startswith("/"):
        url = f"/{url}"
    base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    return f"{base}{url}"


def coerce_duration(value: Any) -> int:
    try:
        dur = float(value)
    except (TypeError, ValueError):
        return 5
    if dur <= 0:
        return 5
    return int(round(dur))


def coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def merge_urls(existing: Any, new_val: Optional[str]) -> List[str]:
    merged: list[str] = []
    if isinstance(existing, list):
        for url in existing:
            if isinstance(url, str) and url and url not in merged:
                merged.append(url)
    if new_val and new_val not in merged:
        merged.append(new_val)
    return merged


def map_provider_status(value: Optional[str]) -> VideoGenerationTaskStatus:
    if value in (ProviderTaskStatus.SUCCESS.value, ProviderTaskStatus.COMPLETED.value):
        return VideoGenerationTaskStatus.SUCCEEDED
    if value == ProviderTaskStatus.FAILED.value:
        return VideoGenerationTaskStatus.FAILED
    if value == ProviderTaskStatus.TIMEOUT.value:
        return VideoGenerationTaskStatus.TIMEOUT
    return VideoGenerationTaskStatus.PROCESSING


def load_parameters(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def normalize_submission_options(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts = dict(options or {})
    return_last_frame = opts.get("return_last_frame")
    opts["return_last_frame"] = (
        True if return_last_frame is None else bool(return_last_frame)
    )
    use_end_frame = opts.get("use_end_frame")
    opts["use_end_frame"] = False if use_end_frame is None else bool(use_end_frame)
    opts["fps"] = coerce_int(opts.get("fps"), 24)
    opts["resolution"] = str(opts.get("resolution") or "720p")
    return opts


def build_selection_map(
    selections: Optional[List[Dict[str, Any]]],
) -> Dict[int, Dict[str, Any]]:
    selection_by_index: Dict[int, Dict[str, Any]] = {}
    for item in selections or []:
        if not isinstance(item, dict):
            continue
        raw_idx = item.get("frame_index")
        try:
            selection_by_index[int(raw_idx)] = item
        except (TypeError, ValueError):
            continue
    return selection_by_index


def resolve_frame_urls(
    frame: Dict[str, Any],
    selection: Dict[str, Any],
    use_end_frame: bool,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    selection_has_start = "start_image_url" in selection
    selection_has_end = "end_image_url" in selection
    raw_start_url = selection.get("start_image_url")
    raw_end_url = selection.get("end_image_url")
    end_explicit_none = selection_has_end and not raw_end_url

    if not raw_start_url:
        raw_start_url = (
            frame.get("start_image_url")
            or frame.get("image_url")
            or (
                (frame.get("start_image_urls") or [None])[0]
                if isinstance(frame.get("start_image_urls"), list)
                else None
            )
            or frame.get("end_image_url")
            or (
                (frame.get("end_image_urls") or [None])[0]
                if isinstance(frame.get("end_image_urls"), list)
                else None
            )
            or ""
        )

    if (
        not use_end_frame
        or end_explicit_none
        or (selection_has_start and not selection_has_end)
    ):
        raw_end_url = ""
    elif not raw_end_url:
        raw_end_url = (
            frame.get("end_image_url")
            or (
                (frame.get("end_image_urls") or [None])[0]
                if isinstance(frame.get("end_image_urls"), list)
                else None
            )
            or ""
        )

    if not raw_start_url:
        return None, None, "未找到首帧"

    start_url = abs_url(str(raw_start_url))
    end_url = abs_url(str(raw_end_url)) if raw_end_url else None
    return start_url, end_url, None


def resolve_prompt(
    frame: Dict[str, Any],
    prompt_override: Optional[str],
) -> Optional[str]:
    if prompt_override:
        return str(prompt_override).strip() or None
    prompt_value = (frame.get("ai_prompt") or frame.get("description") or "").strip()
    return prompt_value or None


def build_parameters_payload(
    prompt: Optional[str],
    start_url: Optional[str],
    end_url: Optional[str],
    duration: int,
    opts: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "prompt": prompt,
        "image_url": start_url,
        "end_image_url": end_url,
        "duration": duration,
        "fps": opts.get("fps"),
        "resolution": opts.get("resolution"),
        "ratio": opts.get("ratio"),
        "watermark": opts.get("watermark"),
        "seed": opts.get("seed"),
        "camera_fixed": opts.get("camera_fixed"),
        "camera_control": opts.get("camera_control"),
        "service_tier": opts.get("service_tier"),
        "execution_expires_after": opts.get("execution_expires_after"),
        "return_last_frame": opts.get("return_last_frame"),
    }
