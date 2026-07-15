"""Persist auditable provider submission failures for Timeline video tasks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.models.video_generation_task import VideoGenerationTaskStatus
from app.services.video.video_task_generation_metadata import (
    build_video_generation_metadata,
)
from app.services.video.video_task_utils import build_parameters_payload

_REQUEST_ID_PATTERN = re.compile(r"request id:\s*([a-zA-Z0-9-]+)", re.IGNORECASE)
_REFERENCE_PRIVACY_TOKENS = (
    "inputimagesensitivecontentdetected.privacyinformation",
    "input image may contain real person",
)


@dataclass(frozen=True, slots=True)
class TimelineVideoSubmissionAttempt:
    task_id: int
    user_id: int
    prompt: str | None
    start_url: str | None
    end_url: str | None
    reference_images: list[str] | None
    target_duration_seconds: float
    provider_duration_seconds: int
    model_type: str
    opts: dict[str, Any]
    timeline_rework: dict[str, Any]


def persist_timeline_video_submission_failure(
    repo: Any,
    *,
    attempt: TimelineVideoSubmissionAttempt,
    error_message: str,
    response: Any | None,
) -> None:
    provider, model, model_type = _provider_identity(response, attempt)
    failure = classify_video_submission_failure(error_message)
    params = build_parameters_payload(
        attempt.prompt,
        attempt.start_url,
        attempt.end_url,
        attempt.reference_images,
        attempt.provider_duration_seconds,
        attempt.opts,
        target_duration_seconds=round(attempt.target_duration_seconds, 3),
        provider_duration_seconds=attempt.provider_duration_seconds,
        timeline_rework=attempt.timeline_rework,
    )
    params["submission_failure"] = failure
    metadata = build_video_generation_metadata(
        provider,
        model,
        None,
        model_type,
        params,
    )
    metadata["submission_failure"] = failure
    repo.create(
        task_id=attempt.task_id,
        script_id=None,
        frame_index=None,
        user_id=attempt.user_id,
        provider=provider,
        provider_task_id="",
        model=model,
        model_type=model_type,
        prompt=attempt.prompt,
        parameters=_json(params),
        generation_metadata=metadata,
        status=VideoGenerationTaskStatus.FAILED,
        error_message=error_message,
    )


def classify_video_submission_failure(error_message: str) -> dict[str, Any]:
    text = str(error_message or "")
    lowered = text.lower()
    if is_reference_privacy_failure(text):
        category, code, retryable = (
            "input_rejected",
            "reference_privacy_rejected",
            False,
        )
    elif "accountoverdueerror" in lowered or "overdue balance" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "account_overdue",
            False,
        )
    elif "insufficient balance" in lowered or "payment required" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "insufficient_balance",
            False,
        )
    elif "401" in lowered or "unauthorized" in lowered or "invalid api key" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "authentication_failed",
            False,
        )
    elif "403" in lowered or "forbidden" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "provider_forbidden",
            False,
        )
    elif "429" in lowered or "rate limit" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "rate_limited",
            True,
        )
    elif any(token in lowered for token in ("timeout", "502", "503", "504")):
        category, code, retryable = (
            "external_dependency_unavailable",
            "provider_unavailable",
            True,
        )
    elif "未返回任务id" in lowered:
        category, code, retryable = (
            "external_dependency_unavailable",
            "provider_task_id_missing",
            True,
        )
    else:
        category, code, retryable = (
            "external_dependency_unavailable",
            "provider_submission_failed",
            True,
        )
    result: dict[str, Any] = {
        "category": category,
        "code": code,
        "retryable": retryable,
    }
    request_id = _provider_request_id(text)
    if request_id:
        result["provider_request_id"] = request_id
    return result


def is_reference_privacy_failure(error_message: str) -> bool:
    lowered = str(error_message or "").lower()
    return any(token in lowered for token in _REFERENCE_PRIVACY_TOKENS)


def _provider_identity(
    response: Any | None,
    attempt: TimelineVideoSubmissionAttempt,
) -> tuple[str, str | None, str]:
    requested_provider, requested_model = _requested_provider_model(
        attempt.opts.get("model")
    )
    provider = _text(getattr(response, "provider", None)) or requested_provider
    model = _text(getattr(response, "model", None)) or requested_model
    model_type = getattr(response, "model_type", None)
    if hasattr(model_type, "value"):
        model_type = model_type.value
    return provider or "unknown", model, _text(model_type) or attempt.model_type


def _requested_provider_model(value: Any) -> tuple[str | None, str | None]:
    model = _text(value)
    if not model or ":" not in model:
        return None, model
    provider, model_id = model.split(":", 1)
    return _text(provider), _text(model_id)


def _provider_request_id(error_message: str) -> str | None:
    match = _REQUEST_ID_PATTERN.search(error_message)
    return match.group(1) if match else None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _json(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)
