"""Queue Timeline-derived grid storyboard sheet generation tasks."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline import (
    TimelineClipStoryboardGenerateRequest,
    TimelineClipStoryboardGenerateResponse,
    TimelineStoryboardGridGenerateRequest,
    TimelineStoryboardGridGenerateResponse,
)
from app.services.storyboard.clip_storyboard_context import (
    build_clip_storyboard_context,
)
from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_clip_storyboard_panels,
    build_clip_storyboard_sheet_prompt,
    build_grid_storyboard_panels,
    grid_layout,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class GridStoryboardSheetService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.tasks = TaskRepository(db)

    def queue_grid_sheet(
        self,
        timeline_id: int,
        payload: TimelineStoryboardGridGenerateRequest,
        current_user: User,
    ) -> TimelineStoryboardGridGenerateResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )

        task_payload = self._task_payload(timeline, payload)
        task = self.tasks.create(
            target_business_id=timeline.business_id,
            title=f"Timeline grid storyboard - {timeline.id}",
            description="Generate a grid storyboard sheet from Timeline clips",
            task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
            prompt=task_payload["sheet_prompt"],
            parameters=json.dumps(task_payload, ensure_ascii=False),
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(task)
        dispatch_grid_storyboard_sheet_task(task, task_payload, current_user)
        return TimelineStoryboardGridGenerateResponse(
            task_id=task.id, status=_status_value(task.status)
        )

    def queue_clip_sheet(
        self,
        timeline_id: int,
        clip_id: str,
        payload: TimelineClipStoryboardGenerateRequest,
        current_user: User,
    ) -> TimelineClipStoryboardGenerateResponse:
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
                detail="clip storyboard requires a video clip",
            )

        task_payload = self._clip_task_payload(timeline, clip_id, clip, payload)
        task = self.tasks.create(
            target_business_id=timeline.business_id,
            title=f"Timeline clip storyboard - {clip_id}",
            description="Generate a storyboard sheet for one selected Timeline clip",
            task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
            prompt=task_payload["sheet_prompt"],
            parameters=json.dumps(task_payload, ensure_ascii=False),
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(task)
        dispatch_grid_storyboard_sheet_task(task, task_payload, current_user)
        return TimelineClipStoryboardGenerateResponse(
            task_id=task.id, status=_status_value(task.status)
        )

    def _task_payload(
        self,
        timeline: Timeline,
        payload: TimelineStoryboardGridGenerateRequest,
    ) -> dict[str, Any]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        panels = build_grid_storyboard_panels(spec, payload.panel_count)
        if not panels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline video clips missing",
            )

        layout = grid_layout(payload.panel_count)
        sheet_prompt = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_GRID_SHEET.value,
            {
                "layout_label": layout.label,
                "panel_count": layout.panel_count,
                "style": payload.style,
                "panel_briefs": [
                    panel.get("storyboard_panel_prompt") or "" for panel in panels
                ],
            },
        )
        return {
            "kind": "timeline_storyboard_grid",
            "timeline_id": timeline.id,
            "timeline_business_id": timeline.business_id,
            "timeline_version": timeline.version,
            "expected_version": payload.expected_version,
            "panel_count": layout.panel_count,
            "columns": layout.columns,
            "rows": layout.rows,
            "style": payload.style,
            "model": payload.model,
            "generation_profile": payload.generation_profile,
            "size": payload.size,
            "aspect_ratio": payload.aspect_ratio,
            "width": payload.width,
            "height": payload.height,
            "reference_images": payload.reference_images or [],
            "panels": panels,
            "sheet_prompt": sheet_prompt,
        }

    def _clip_task_payload(
        self,
        timeline: Timeline,
        clip_id: str,
        clip: dict[str, Any],
        payload: TimelineClipStoryboardGenerateRequest,
    ) -> dict[str, Any]:
        panels = build_clip_storyboard_panels(clip, payload.panel_count)
        if not panels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="clip storyboard panels missing",
            )

        context = build_clip_storyboard_context(
            self.db,
            timeline=timeline,
            clip=clip,
            panels=panels,
            request_reference_images=payload.reference_images or [],
        )
        panels = context.panels
        layout = grid_layout(payload.panel_count)
        sheet_prompt = build_clip_storyboard_sheet_prompt(panels, style=payload.style)
        return {
            "kind": "timeline_clip_storyboard",
            "timeline_id": timeline.id,
            "timeline_business_id": timeline.business_id,
            "timeline_version": timeline.version,
            "expected_version": payload.expected_version,
            "clip_id": clip_id,
            "panel_count": layout.panel_count,
            "columns": layout.columns,
            "rows": layout.rows,
            "style": payload.style,
            "model": payload.model,
            "generation_profile": payload.generation_profile,
            "size": payload.size,
            "aspect_ratio": payload.aspect_ratio,
            "width": payload.width,
            "height": payload.height,
            "reference_images": context.reference_images,
            "bound_context": context.bound_context,
            "panels": panels,
            "sheet_prompt": sheet_prompt,
        }

    def _get_timeline_or_404(self, timeline_id: int, current_user: User) -> Timeline:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=self._story_owner_filter(current_user),
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

    @staticmethod
    def _story_owner_filter(current_user: User) -> int | None:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id


def dispatch_grid_storyboard_sheet_task(
    task,
    payload: dict[str, Any],
    current_user: User,
) -> None:
    from app.services.task_worker_grid_storyboard import (
        grid_storyboard_sheet_generate_task,
    )

    grid_storyboard_sheet_generate_task.delay(task.id, payload, current_user.id)


def _status_value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)
