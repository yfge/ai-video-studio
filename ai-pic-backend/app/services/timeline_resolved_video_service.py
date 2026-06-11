"""Read model for Timeline video sources visible to operators."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline_resolved_videos import (
    TimelineResolvedVideoItem,
    TimelineResolvedVideoListResponse,
)
from app.services.render.timeline_render_clips import TimelineClipResolver
from app.services.render.timeline_render_types import TimelineClipVideo
from app.services.timeline_clip_video_rework_helpers import (
    clip_duration_seconds,
    maybe_int,
    story_owner_filter,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineResolvedVideoService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.tasks = TaskRepository(db)
        self.resolver = TimelineClipResolver(db)

    def list_resolved_videos(
        self,
        timeline_id: int,
        current_user: User,
    ) -> TimelineResolvedVideoListResponse:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )

        resolved, missing = self.resolver.resolve(timeline)
        resolved_by_clip = {item.clip_id: item for item in resolved}
        missing_by_clip = {str(item.get("clip_id") or ""): item for item in missing}
        tasks_by_clip = self._active_tasks_by_clip(timeline.business_id, current_user)
        items = [
            self._item_for_clip(
                clip,
                resolved_by_clip=resolved_by_clip,
                missing_by_clip=missing_by_clip,
                tasks_by_clip=tasks_by_clip,
            )
            for clip in self._timeline_video_clips(timeline.spec)
        ]
        missing_count = sum(1 for item in items if item.status == "missing")
        generating_count = sum(1 for item in items if item.status == "generating")
        return TimelineResolvedVideoListResponse(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            ready=bool(items) and missing_count == 0 and generating_count == 0,
            video_clip_count=len(items),
            missing_clip_count=missing_count,
            generating_clip_count=generating_count,
            items=items,
        )

    def _item_for_clip(
        self,
        clip: dict[str, Any],
        *,
        resolved_by_clip: dict[str, TimelineClipVideo],
        missing_by_clip: dict[str, dict[str, Any]],
        tasks_by_clip: dict[str, Task],
    ) -> TimelineResolvedVideoItem:
        clip_id = str(clip.get("clip_id") or clip.get("id") or "unknown")
        resolved = resolved_by_clip.get(clip_id)
        if resolved is not None:
            return TimelineResolvedVideoItem(
                clip_id=clip_id,
                status="ready",
                url=resolved.url,
                source=resolved.source,
                scene_id=resolved.scene_id,
                scene_number=resolved.scene_number,
                start_ms=resolved.start_ms,
                end_ms=resolved.end_ms,
                duration_seconds=resolved.duration_seconds,
            )

        task = tasks_by_clip.get(clip_id)
        missing = missing_by_clip.get(clip_id, {})
        if task is not None:
            return TimelineResolvedVideoItem(
                clip_id=clip_id,
                status="generating",
                reason="generating",
                scene_id=missing.get("scene_id") or clip.get("scene_id"),
                scene_number=missing.get("scene_number") or clip.get("scene_number"),
                start_ms=missing.get("start_ms") or maybe_int(clip.get("start_ms")),
                end_ms=missing.get("end_ms") or maybe_int(clip.get("end_ms")),
                duration_seconds=clip_duration_seconds(clip),
                task_id=task.id,
                task_type=self._enum_value(task.task_type),
                task_status=self._enum_value(task.status),
                task_title=task.title,
            )

        return TimelineResolvedVideoItem(
            clip_id=clip_id,
            status="missing",
            reason=str(missing.get("reason") or "missing_video_url"),
            scene_id=missing.get("scene_id") or clip.get("scene_id"),
            scene_number=missing.get("scene_number") or clip.get("scene_number"),
            start_ms=missing.get("start_ms") or maybe_int(clip.get("start_ms")),
            end_ms=missing.get("end_ms") or maybe_int(clip.get("end_ms")),
            duration_seconds=clip_duration_seconds(clip),
        )

    def _active_tasks_by_clip(
        self,
        timeline_business_id: str,
        current_user: User,
    ) -> dict[str, Task]:
        result: dict[str, Task] = {}
        for task in self.tasks.list_active_for_target(
            user_id=current_user.id,
            target_business_id=timeline_business_id,
        ):
            clip_id = self._clip_id_from_task(task)
            if clip_id and clip_id not in result:
                result[clip_id] = task
        return result

    @staticmethod
    def _clip_id_from_task(task: Task) -> str | None:
        if not task.parameters:
            return None
        try:
            loaded = json.loads(task.parameters)
        except (TypeError, ValueError):
            return None
        if not isinstance(loaded, dict):
            return None
        clip_id = loaded.get("clip_id")
        return clip_id.strip() if isinstance(clip_id, str) and clip_id.strip() else None

    @staticmethod
    def _timeline_video_clips(spec: Any) -> list[dict[str, Any]]:
        if not isinstance(spec, dict):
            return []
        clips: list[dict[str, Any]] = []
        for track in spec.get("tracks") or []:
            if not isinstance(track, dict):
                continue
            if str(track.get("track_type") or track.get("type") or "") != "video":
                continue
            clips.extend(
                clip for clip in track.get("clips") or [] if isinstance(clip, dict)
            )
        return clips

    @staticmethod
    def _enum_value(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)
