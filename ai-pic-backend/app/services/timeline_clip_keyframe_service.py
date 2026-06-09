"""Queue Timeline clip start/end keyframe generation."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline_clip_keyframes import (
    TimelineClipKeyframeGenerateRequest,
    TimelineClipKeyframeGenerateResponse,
)
from app.services.storyboard.clip_storyboard_context import (
    build_clip_storyboard_context,
)
from app.services.timeline_clip_keyframe_dispatch import (
    dispatch_timeline_clip_keyframe_task,
)
from app.services.timeline_clip_video_rework_helpers import (
    clip_prompt,
    dedupe_strings,
    story_owner_filter,
    string_value,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineClipKeyframeService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.tasks = TaskRepository(db)

    def queue_keyframes(
        self,
        timeline_id: int,
        clip_id: str,
        payload: TimelineClipKeyframeGenerateRequest,
        current_user: User,
    ) -> TimelineClipKeyframeGenerateResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )
        clip = self._clip_or_404(timeline, clip_id)
        if clip.get("track_type") != "video":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="clip keyframes require a video clip",
            )
        task_payload = self._task_payload(timeline, clip_id, clip, payload)
        task = self.tasks.create(
            target_business_id=timeline.business_id,
            title=f"Timeline clip keyframes - {clip_id}",
            description="Generate start and end keyframes for one Timeline clip",
            task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
            prompt=task_payload["prompt"],
            parameters=json.dumps(task_payload, ensure_ascii=False),
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(task)
        dispatch_timeline_clip_keyframe_task(task, task_payload, current_user)
        return TimelineClipKeyframeGenerateResponse(
            task_id=task.id, status=_status_value(task.status)
        )

    def _task_payload(
        self,
        timeline: Timeline,
        clip_id: str,
        clip: dict[str, Any],
        payload: TimelineClipKeyframeGenerateRequest,
    ) -> dict[str, Any]:
        prompt = _clip_keyframe_prompt(clip, payload.prompt)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="clip keyframes require a prompt",
            )
        context = build_clip_storyboard_context(
            self.db,
            timeline=timeline,
            clip=clip,
            panels=[],
            request_reference_images=payload.reference_images or [],
            request_character_virtual_ip_ids=payload.character_virtual_ip_ids or [],
            request_character_reference_images=payload.character_reference_images or [],
            request_environment_reference_images=payload.environment_reference_images
            or [],
        )
        frames = _keyframe_prompts(prompt)
        return {
            "kind": "timeline_clip_keyframes",
            "timeline_id": timeline.id,
            "timeline_business_id": timeline.business_id,
            "timeline_version": timeline.version,
            "expected_version": payload.expected_version,
            "clip_id": clip_id,
            "prompt": prompt,
            "model": payload.model,
            "generation_profile": payload.generation_profile,
            "size": payload.size,
            "aspect_ratio": payload.aspect_ratio,
            "width": payload.width,
            "height": payload.height,
            "reference_images": context.reference_images,
            "character_virtual_ip_ids": _dedupe_ints(
                payload.character_virtual_ip_ids or []
            ),
            "character_reference_images": dedupe_strings(
                payload.character_reference_images or []
            ),
            "environment_reference_images": dedupe_strings(
                payload.environment_reference_images or []
            ),
            "bound_context": context.bound_context,
            "keyframe_roles": [frame["role"] for frame in frames],
            "frames": frames,
        }

    def _get_timeline_or_404(self, timeline_id: int, current_user: User) -> Timeline:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        return timeline

    @staticmethod
    def _clip_or_404(timeline: Timeline, clip_id: str) -> dict[str, Any]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        for track in spec.get("tracks") or []:
            if not isinstance(track, dict):
                continue
            track_type = track.get("track_type") or track.get("type")
            for clip in track.get("clips") or []:
                if (
                    isinstance(clip, dict)
                    and (clip.get("clip_id") or clip.get("id")) == clip_id
                ):
                    return {**clip, "track_type": clip.get("track_type") or track_type}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="timeline clip not found",
        )


def _clip_keyframe_prompt(clip: dict[str, Any], override: str | None) -> str | None:
    prompt = clip_prompt(clip, override)
    if prompt:
        return prompt
    source_refs = (
        clip.get("source_refs") if isinstance(clip.get("source_refs"), dict) else {}
    )
    shot_plan = source_refs.get("timeline_shot_plan")
    if isinstance(shot_plan, dict):
        for key in ("visual_prompt", "video_prompt", "storyboard_panel_prompt"):
            value = string_value(shot_plan.get(key))
            if value:
                return value
    return None


def _keyframe_prompts(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "start_frame",
            "prompt": (
                "Opening keyframe for this video clip. Keep characters, "
                f"environment, wardrobe, and lighting consistent. {prompt}"
            ),
        },
        {
            "role": "end_frame",
            "prompt": (
                "Ending keyframe for this video clip. Preserve the same IP "
                f"and environment continuity while landing the motion. {prompt}"
            ),
        },
    ]


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


def _status_value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)
