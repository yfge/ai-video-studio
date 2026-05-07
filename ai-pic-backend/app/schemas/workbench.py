from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkbenchMetrics(BaseModel):
    pending_tasks: int
    running_tasks: int
    failed_tasks: int
    continuable_episodes: int


class WorkbenchEpisode(BaseModel):
    story_id: int
    story_business_id: str
    story_title: str
    episode_id: int
    episode_business_id: str
    episode_number: int
    episode_title: str
    latest_script_id: Optional[int] = None
    latest_script_business_id: Optional[str] = None
    current_stage: str
    current_stage_label: str
    script_ready: bool
    timeline_ready: bool
    storyboard_ready: bool
    updated_at: datetime


class WorkbenchTask(BaseModel):
    id: int
    business_id: str
    title: str
    task_type: str
    status: str
    progress: int
    progress_detail: Optional[str] = None
    error_message: Optional[str] = None
    target_business_id: Optional[str] = None
    updated_at: datetime


class WorkbenchSummary(BaseModel):
    metrics: WorkbenchMetrics
    recent_episodes: list[WorkbenchEpisode]
    task_queue: list[WorkbenchTask]
