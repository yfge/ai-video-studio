"""
Google Veo helper utilities.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from app.services.video.video_duration import resolve_duration_ceil


def normalize_operation_path(name: str) -> str:
    op = (name or "").lstrip("/")
    if op.startswith("v1beta/"):
        op = op[len("v1beta/") :]
    return op


def normalize_ratio(ratio: Optional[str]) -> Optional[str]:
    if not ratio:
        return None
    raw = str(ratio).strip().lower().replace("x", ":")
    if raw in {"16:9", "9:16"}:
        return raw
    return None


def normalize_resolution(resolution: Optional[str]) -> Optional[str]:
    if not resolution:
        return None
    raw = str(resolution).strip().lower()
    if "x" in raw:
        parts = raw.split("x", 1)
        try:
            width = int(parts[0])
            height = int(parts[1])
        except (TypeError, ValueError):
            return None
        if (width, height) == (1280, 720):
            return "720p"
        if (width, height) == (1920, 1080):
            return "1080p"
    if raw.endswith("p") and raw[:-1].isdigit():
        return raw
    return None


def resolve_duration(
    model_id: str,
    duration: Optional[int],
    *,
    resolution: Optional[str] = None,
) -> Optional[int]:
    if duration is None:
        return None
    try:
        dur = int(duration)
    except (TypeError, ValueError):
        return None
    mid = (model_id or "").lower()
    res = normalize_resolution(resolution) if resolution else None
    if "veo-3.1" in mid:
        options = [8] if res == "1080p" else [4, 6, 8]
    elif "veo-3.0" in mid:
        options = [8]
    elif "veo-2.0" in mid:
        options = [5, 6, 8]
    else:
        options = [4, 6, 8]
    return resolve_duration_ceil(target_seconds=dur, allowed_durations=options).provider_seconds


def supports_reference_images(model_id: str) -> bool:
    return "veo-3.1" in (model_id or "").lower()


def append_api_key(url: str, api_key: str) -> str:
    if not url or not api_key:
        return url
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return url
    query = dict(parse_qsl(parsed.query))
    if "key" not in query:
        query["key"] = api_key
    return urlunparse(parsed._replace(query=urlencode(query)))


def extract_video_uri(response: Dict[str, Any]) -> Optional[str]:
    root = response.get("response") or {}
    videos = root.get("videos")
    if isinstance(videos, list) and videos:
        first = videos[0] if isinstance(videos[0], dict) else None
        if first:
            return first.get("gcsUri") or first.get("gcs_uri")
    generate = root.get("generateVideoResponse") or root.get("generate_video_response")
    if not generate:
        generate = root
    candidates = (
        generate.get("generatedSamples")
        or generate.get("generated_samples")
        or generate.get("generatedVideos")
        or generate.get("generated_videos")
        or []
    )
    if not candidates:
        return None
    first = candidates[0] if isinstance(candidates, list) else candidates
    video = first.get("video") if isinstance(first, dict) else None
    if isinstance(video, dict):
        return video.get("uri") or video.get("url")
    if isinstance(video, str):
        return video
    if isinstance(first, dict):
        return first.get("uri") or first.get("url")
    return None


def _truncate_one_line(value: str, max_chars: int) -> str:
    if not value:
        return ""
    compact = " ".join(str(value).split())
    if max_chars > 0 and len(compact) > max_chars:
        return compact[:max_chars] + "…"
    return compact


def _extract_google_error_message(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    err = payload.get("error")
    if isinstance(err, dict):
        status = err.get("status")
        message = err.get("message")
        if status and message:
            return f"{status}: {message}"
        if message:
            return str(message)
        if status:
            return str(status)
    message = payload.get("message")
    if message:
        return str(message)
    return None


def format_http_status_error(
    exc: httpx.HTTPStatusError,
    *,
    label: str = "Google API",
    max_body_chars: int = 800,
) -> str:
    response = exc.response
    detail = None
    try:
        detail = _extract_google_error_message(response.json())
    except Exception:
        detail = None

    if not detail:
        body = (response.text or "").strip()
        if body:
            detail = body

    if detail:
        return f"{label} HTTP {response.status_code}: {_truncate_one_line(detail, max_body_chars)}"
    return f"{label} HTTP {response.status_code}: {str(exc)}"
