"""Operator workbench aggregation service."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.models.script import Episode, Script
from app.models.task import Task, TaskStatus
from app.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.workbench_repository import WorkbenchRepository
from app.schemas.workbench import (
    WorkbenchEpisode,
    WorkbenchMetrics,
    WorkbenchSummary,
    WorkbenchTask,
)
from sqlalchemy.orm import Session


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _latest_script(scripts: list[Script]) -> Script | None:
    active = [script for script in scripts if not getattr(script, "is_deleted", False)]
    if not active:
        return None
    return sorted(
        active,
        key=lambda script: (
            script.updated_at or script.created_at or datetime.min,
            script.id,
        ),
        reverse=True,
    )[0]


def _timeline_row_ready(timeline: Timeline | None) -> bool:
    # Timeline 表是唯一事实来源；episode.extra_metadata 里的旧 audio_timeline
    # 不再参与判定，避免 timeline 删除后 dashboard 仍显示就绪。
    return timeline is not None and not getattr(timeline, "is_deleted", False)


def _storyboard_ready(script: Script | None) -> bool:
    if script is None:
        return False
    storyboard = _as_dict(_as_dict(script.extra_metadata).get("storyboard"))
    frames = storyboard.get("frames")
    return isinstance(frames, list) and len(frames) > 0


def _episode_stage(script_ready: bool, timeline_ready: bool, storyboard_ready: bool):
    if storyboard_ready:
        return "storyboard_ready", "分镜就绪"
    if timeline_ready:
        return "timeline_ready", "时间轴就绪"
    if script_ready:
        return "script_ready", "剧本就绪"
    return "script_pending", "待生成剧本"


def _task_parameters(task: Task) -> dict[str, Any]:
    if not task.parameters:
        return {}
    try:
        loaded = json.loads(task.parameters)
    except (TypeError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _task_progress(task: Task) -> int:
    params = _task_parameters(task)
    raw_progress = params.get("progress") or params.get("progress_percent")
    try:
        return max(0, min(100, int(float(raw_progress))))
    except (TypeError, ValueError):
        pass
    if task.status == TaskStatus.COMPLETED:
        return 100
    if task.status == TaskStatus.PROCESSING:
        return 50
    return 0


class WorkbenchService:
    def __init__(self, db: Session):
        self.repository = WorkbenchRepository(db)
        self.timelines = TimelineRepository(db)

    def summary_for_user(self, user_id: int) -> WorkbenchSummary:
        status_counts = self.repository.count_tasks_by_status(user_id)
        episodes = self.repository.list_recent_episodes(user_id=user_id)
        tasks = self.repository.list_recent_tasks(user_id=user_id)

        return WorkbenchSummary(
            metrics=WorkbenchMetrics(
                pending_tasks=status_counts.get(TaskStatus.PENDING, 0),
                running_tasks=status_counts.get(TaskStatus.PROCESSING, 0),
                failed_tasks=status_counts.get(TaskStatus.FAILED, 0),
                continuable_episodes=self.repository.count_continuable_episodes(
                    user_id
                ),
            ),
            recent_episodes=[self._serialize_episode(episode) for episode in episodes],
            task_queue=[self._serialize_task(task) for task in tasks],
        )

    def _serialize_episode(self, episode: Episode) -> WorkbenchEpisode:
        script = _latest_script(list(episode.scripts or []))
        script_ready = script is not None
        timeline = (
            self.timelines.get_latest_for_episode_script(
                episode_id=episode.id,
                script_id=script.id,
            )
            if script is not None
            else None
        )
        timeline_ready = _timeline_row_ready(timeline)
        storyboard_ready = _storyboard_ready(script)
        stage, label = _episode_stage(script_ready, timeline_ready, storyboard_ready)
        story = episode.story

        return WorkbenchEpisode(
            story_id=story.id,
            story_business_id=story.business_id,
            story_title=story.title,
            episode_id=episode.id,
            episode_business_id=episode.business_id,
            episode_number=episode.episode_number,
            episode_title=episode.title,
            latest_script_id=script.id if script else None,
            latest_script_business_id=script.business_id if script else None,
            timeline_id=timeline.id if timeline else None,
            timeline_version=timeline.version if timeline else None,
            timeline_status=timeline.status if timeline else None,
            source_audio_timeline_version=(
                timeline.source_audio_timeline_version if timeline else None
            ),
            current_stage=stage,
            current_stage_label=label,
            script_ready=script_ready,
            timeline_ready=timeline_ready,
            storyboard_ready=storyboard_ready,
            updated_at=episode.updated_at or episode.created_at,
        )

    def _serialize_task(self, task: Task) -> WorkbenchTask:
        updated_at = task.updated_at or task.created_at
        progress_detail = task.description
        if task.status in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
            progress_detail = task.error_message or task.description
        return WorkbenchTask(
            id=task.id,
            business_id=task.business_id,
            title=task.title,
            task_type=(
                task.task_type.value
                if hasattr(task.task_type, "value")
                else str(task.task_type)
            ),
            status=(
                task.status.value if hasattr(task.status, "value") else str(task.status)
            ),
            progress=_task_progress(task),
            progress_detail=progress_detail,
            error_message=task.error_message,
            target_business_id=task.target_business_id,
            updated_at=updated_at,
        )
