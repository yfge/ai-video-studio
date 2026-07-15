"""Small helpers for Timeline clip video rework queueing."""

from __future__ import annotations

from math import gcd
from typing import Any

from app.models.timeline import Timeline
from app.models.user import User


def clip_duration_seconds(clip: dict[str, Any]) -> float:
    start_ms = maybe_int(clip.get("start_ms"))
    end_ms = maybe_int(clip.get("end_ms"))
    if start_ms is not None and end_ms is not None and end_ms > start_ms:
        return max((end_ms - start_ms) / 1000, 0.1)
    duration_ms = maybe_int(clip.get("duration_ms"))
    if duration_ms and duration_ms > 0:
        return max(duration_ms / 1000, 0.1)
    duration_seconds = maybe_float(clip.get("duration_seconds"))
    return max(duration_seconds, 0.1) if duration_seconds else 5.0


def render_preset(timeline: Timeline) -> dict[str, Any]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    return {
        "fps": spec.get("fps") or 24,
        "resolution": spec.get("resolution") or "1080x1920",
    }


def render_ratio(timeline: Timeline) -> str | None:
    resolution = render_preset(timeline).get("resolution")
    if not isinstance(resolution, str) or "x" not in resolution.lower():
        return None
    width_text, height_text = resolution.lower().split("x", 1)
    try:
        width = int(width_text)
        height = int(height_text)
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def story_owner_filter(current_user: User) -> int | None:
    if getattr(current_user, "is_superuser", False) or getattr(
        current_user, "is_admin", False
    ):
        return None
    return current_user.id


def string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def clip_prompt(clip: dict[str, Any], override: str | None) -> str | None:
    if override and override.strip():
        return override.strip()
    for key in ("ai_prompt", "prompt", "description", "text", "label"):
        value = string_value(clip.get(key))
        if value:
            return value
    return None


def maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def dedupe_strings(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip() and value.strip() not in deduped:
            deduped.append(value.strip())
    return deduped


def requires_operator_review(clip: dict[str, Any]) -> bool:
    refs = clip.get("source_refs")
    review = refs.get("human_review") if isinstance(refs, dict) else None
    if not isinstance(review, dict) or not review.get("required"):
        return False
    return str(review.get("status") or "").lower() not in {
        "approved",
        "confirmed",
        "passed",
    }
