"""Provider-specific duration adaptation for Timeline video submissions."""

from __future__ import annotations

from app.services.providers.base import AIResponse
from app.services.video.video_capabilities import CapabilityMatch

_AUDIT_KEYS = (
    "duration",
    "target_duration_seconds",
    "provider_duration_seconds",
    "allowed_durations",
    "capability_source",
)


def attach_duration_resolution(
    response: AIResponse,
    match: CapabilityMatch,
) -> AIResponse:
    data = dict(response.data) if isinstance(response.data, dict) else {}
    data.update(
        {
            "duration": match.provider_duration_seconds,
            "target_duration_seconds": match.target_duration_seconds,
            "provider_duration_seconds": match.provider_duration_seconds,
            "allowed_durations": match.allowed_durations,
            "capability_source": match.capability_source,
        }
    )
    response.data = data
    return response


def copy_duration_resolution(source: AIResponse, target: AIResponse) -> AIResponse:
    source_data = source.data if isinstance(source.data, dict) else {}
    target_data = dict(target.data) if isinstance(target.data, dict) else {}
    target_data.update(
        {key: source_data[key] for key in _AUDIT_KEYS if key in source_data}
    )
    target.data = target_data or target.data
    return target
