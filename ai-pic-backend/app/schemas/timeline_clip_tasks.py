"""Schemas for listing in-flight generation tasks of one timeline's clips."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class TimelineClipTaskItem(BaseModel):
    task_id: int
    clip_id: Optional[str] = None
    status: str
    task_type: str
    title: Optional[str] = None


class TimelineClipTaskListResponse(BaseModel):
    items: List[TimelineClipTaskItem]
