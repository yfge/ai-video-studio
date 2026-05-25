"""HTTP-facing Timeline Spec validation guard."""

from __future__ import annotations

from typing import Any

from app.models.script import Episode, Script
from app.models.timeline import Timeline
from app.services.timeline_spec_validation import validate_timeline_spec
from app.services.timeline_spec_validation_types import TimelineSpecValidationError
from fastapi import HTTPException, status


def validate_timeline_spec_or_400(spec: dict[str, Any], **kwargs: Any) -> None:
    try:
        validate_timeline_spec(spec, **kwargs)
    except TimelineSpecValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.to_detail(),
        ) from exc


def validate_new_timeline_spec_or_400(
    spec: dict[str, Any], *, episode: Episode, script: Script
) -> None:
    validate_timeline_spec_or_400(
        spec,
        episode_id=episode.id,
        script_id=script.id,
        expected_version=1,
    )


def validate_persisted_timeline_spec_or_400(timeline: Timeline) -> None:
    validate_timeline_spec_or_400(
        timeline.spec,
        episode_id=timeline.episode_id,
        script_id=timeline.script_id,
        timeline_id=timeline.id,
        expected_version=timeline.version,
        require_timeline_id=True,
    )


def validated_timeline_update_payload_or_400(
    timeline: Timeline,
    payload: Any,
) -> tuple[dict[str, Any], int]:
    updates = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
    next_version = (timeline.version or 0) + 1
    spec_candidate = updates["spec"] if "spec" in updates else timeline.spec
    updates["spec"] = {
        **(spec_candidate if isinstance(spec_candidate, dict) else {}),
        "timeline_id": timeline.id,
        "version": next_version,
    }
    validate_persisted_candidate_or_400(timeline, updates["spec"], next_version)
    return updates, next_version


def validate_persisted_candidate_or_400(
    timeline: Timeline,
    spec: dict[str, Any],
    expected_version: int,
) -> None:
    validate_timeline_spec_or_400(
        spec,
        episode_id=timeline.episode_id,
        script_id=timeline.script_id,
        timeline_id=timeline.id,
        expected_version=expected_version,
        require_timeline_id=True,
    )
