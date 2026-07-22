from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class StoryNovelExportSummary(BaseModel):
    """Lightweight novel export record used for history listing."""

    id: int
    business_id: str
    task_id: Optional[int] = None

    style: str = Field(..., description="输出风格，如 zhihu")
    target_words: int = Field(..., description="目标字数")
    chapter_count: Optional[int] = Field(None, description="章节数")
    total_words: Optional[int] = Field(None, description="实际字数")
    model: Optional[str] = Field(None, description="生成模型（原样）")
    temperature: Optional[float] = Field(None, description="生成温度")

    file_relative_path: Optional[str] = Field(None, description="导出文件相对路径")
    revision_number: int = 0
    lifecycle_status: str = "legacy"
    continuity_status: str = "unchecked"
    adaptation_plan_status: str = "empty"
    created_at: datetime

    class Config:
        from_attributes = True


class StoryNovelExportListResponse(BaseModel):
    items: List[StoryNovelExportSummary]


class StoryNovelChapterResponse(BaseModel):
    business_id: str
    position: int
    title: str
    content_text: str
    summary: Optional[str] = None
    cliffhanger: Optional[str] = None
    review_status: str
    content_hash: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryNovelRevisionResponse(StoryNovelExportSummary):
    story_business_id: Optional[str] = None
    content_hash: Optional[str] = None
    story_snapshot: Optional[dict[str, Any]] = None
    generation_plan: Optional[dict[str, Any]] = None
    continuity_ledger: Optional[dict[str, Any]] = None
    continuity_report: Optional[dict[str, Any]] = None
    adaptation_plan: Optional[dict[str, Any]] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    chapters: List[StoryNovelChapterResponse] = Field(default_factory=list)


class StoryNovelRevisionListResponse(BaseModel):
    items: List[StoryNovelRevisionResponse]
    canonical_business_id: Optional[str] = None


class StoryNovelChapterUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content_text: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = None
    cliffhanger: Optional[str] = None
    expected_updated_at: datetime


class StoryNovelChapterReorderRequest(BaseModel):
    ordered_chapter_business_ids: List[str] = Field(..., min_length=1)
    expected_updated_at: datetime


class StoryNovelContinuityIssueAcceptRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class AdaptationPlanEpisode(BaseModel):
    episode_number: int = Field(..., ge=1, le=100)
    title: str = Field(..., min_length=1, max_length=255)
    source_chapter_business_ids: List[str] = Field(..., min_length=1)
    adaptation_goal: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    plot_points: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    character_arcs: dict[str, Any] = Field(default_factory=dict)
    cliffhanger: Optional[str] = None


class StoryNovelAdaptationPlanUpdateRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
    episodes: List[AdaptationPlanEpisode] = Field(..., min_length=1, max_length=100)


class StoryNovelAdaptationPlanApproveRequest(BaseModel):
    expected_version: int = Field(..., ge=1)


class StoryNovelOperationResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


ContinuitySeverity = Literal["blocking", "warning"]
