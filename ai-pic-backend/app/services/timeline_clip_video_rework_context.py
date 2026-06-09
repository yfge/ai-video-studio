"""Bound visual context for Timeline clip video rework tasks."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineClipVideoReworkTaskRequest
from app.services.storyboard.clip_storyboard_context import (
    ClipStoryboardContext,
    build_clip_storyboard_context,
)
from app.services.timeline_clip_video_rework_helpers import dedupe_strings
from sqlalchemy.orm import Session


def build_video_rework_bound_context(
    db: Session,
    *,
    timeline: Timeline,
    clip: dict[str, Any],
    payload: TimelineClipVideoReworkTaskRequest,
) -> ClipStoryboardContext | None:
    if not _has_bound_context_request(payload):
        return None
    return build_clip_storyboard_context(
        db,
        timeline=timeline,
        clip=clip,
        panels=[],
        request_reference_images=payload.reference_images or [],
        request_character_virtual_ip_ids=payload.character_virtual_ip_ids or [],
        request_character_reference_images=payload.character_reference_images or [],
        request_environment_reference_images=payload.environment_reference_images or [],
    )


def apply_video_rework_bound_context(
    task_payload: dict[str, Any],
    *,
    payload: TimelineClipVideoReworkTaskRequest,
    context: ClipStoryboardContext | None,
    reference_mode: str,
) -> None:
    character_ids = _dedupe_ints(payload.character_virtual_ip_ids or [])
    character_refs = dedupe_strings(payload.character_reference_images or [])
    environment_refs = dedupe_strings(payload.environment_reference_images or [])
    if character_ids:
        task_payload["character_virtual_ip_ids"] = character_ids
    if character_refs:
        task_payload["character_reference_images"] = character_refs
    if environment_refs:
        task_payload["environment_reference_images"] = environment_refs
    if context is None:
        return
    existing_refs = list(task_payload.get("reference_images") or [])
    context_refs = context.reference_images
    if reference_mode in {"clip_storyboard_panel", "storyboard_grid_panel"}:
        merged_refs = [*existing_refs, *context_refs]
    else:
        merged_refs = [*context_refs, *existing_refs]
    if merged_refs:
        task_payload["reference_images"] = dedupe_strings(merged_refs)
    task_payload["bound_context"] = context.bound_context


def _has_bound_context_request(payload: TimelineClipVideoReworkTaskRequest) -> bool:
    return bool(
        payload.character_virtual_ip_ids
        or payload.character_reference_images
        or payload.environment_reference_images
    )


def _dedupe_ints(values: list[int]) -> list[int]:
    deduped: list[int] = []
    for value in values:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in deduped:
            deduped.append(parsed)
    return deduped
