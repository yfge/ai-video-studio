from datetime import datetime
from typing import Any, Dict, Optional

from app.models.task import TaskStatus, TaskType
from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType
    prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None


class TaskResultContext(BaseModel):
    """Stable domain identifiers produced or confirmed by a task."""

    virtual_ip_id: Optional[int] = None
    environment_id: Optional[int] = None
    story_id: Optional[int] = None
    episode_id: Optional[int] = None
    script_id: Optional[int] = None
    timeline_id: Optional[int] = None
    timeline_version: Optional[int] = None
    clip_id: Optional[str] = None
    task_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    business_id: str
    status: TaskStatus
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None
    user_id: int
    target_business_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    progress_detail: Optional[str] = None
    result_context: Optional[TaskResultContext] = None

    class Config:
        from_attributes = True


class TaskList(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    size: int
