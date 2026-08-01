from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from app.schemas.story_novel_longform import StoryNovelCanon
from pydantic import BaseModel, Field, model_validator


class NovelLengthRange(BaseModel):
    min_chars: int = Field(..., strict=True, gt=0)
    target_chars: int = Field(..., strict=True, gt=0)
    max_chars: int = Field(..., strict=True, gt=0)

    @model_validator(mode="after")
    def validate_order(self):
        if not self.min_chars <= self.target_chars <= self.max_chars:
            raise ValueError(
                "length must satisfy min_chars <= target_chars <= max_chars"
            )
        return self


class NovelLengthProfileResponse(NovelLengthRange):
    profile_id: str
    name: str
    count_mode: Literal["non_whitespace_chars"] = "non_whitespace_chars"


class NovelModelPolicy(BaseModel):
    planning_model: Optional[str] = Field(None, min_length=1, max_length=128)
    prose_model: Optional[str] = Field(None, min_length=1, max_length=128)
    audit_model: Optional[str] = Field(None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def normalize_model_ids(self):
        for field in ("planning_model", "prose_model", "audit_model"):
            value = getattr(self, field)
            if value is not None:
                value = value.strip()
                if not value:
                    raise ValueError(f"{field} must not be blank")
                setattr(self, field, value)
        return self


def _validate_legacy_model_matches_policy(model, policy):
    if model and policy and policy.prose_model and model.strip() != policy.prose_model:
        raise ValueError("model must match model_policy.prose_model")


class StoryNovelCreateRevisionRequest(BaseModel):
    style: Literal["prose"] = "prose"
    length_profile_id: str = "standard_serial"
    custom_length_profile: Optional[NovelLengthRange] = None
    chapter_length_overrides: dict[str, NovelLengthRange] = Field(default_factory=dict)
    model: Optional[str] = Field(None, min_length=1, max_length=128)
    model_policy: Optional[NovelModelPolicy] = None
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.5)

    @model_validator(mode="after")
    def validate_model_policy(self):
        _validate_legacy_model_matches_policy(self.model, self.model_policy)
        return self


class StoryNovelLengthSpecUpdateRequest(BaseModel):
    length_profile_id: str
    custom_length_profile: Optional[NovelLengthRange] = None
    chapter_length_overrides: dict[str, NovelLengthRange] = Field(default_factory=dict)
    expected_plan_version: int = Field(..., strict=True, ge=1)
    model: Optional[str] = Field(None, min_length=1, max_length=128)
    model_policy: Optional[NovelModelPolicy] = None

    @model_validator(mode="after")
    def validate_model_policy(self):
        _validate_legacy_model_matches_policy(self.model, self.model_policy)
        return self


class StoryNovelGenerateRevisionRequest(BaseModel):
    target_words: Optional[int] = None
    chapter_count: Optional[int] = None

    def compatibility_warnings(self) -> list[str]:
        ignored = [
            name
            for name in ("target_words", "chapter_count")
            if getattr(self, name) is not None
        ]
        return ["prose 已忽略旧字段: " + ", ".join(ignored)] if ignored else []


class StoryNovelContinuityCheckRequest(BaseModel):
    review_model: Optional[str] = Field(None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def normalize_review_model(self):
        if self.review_model is None:
            return self
        self.review_model = self.review_model.strip()
        if ":" not in self.review_model or not all(self.review_model.split(":", 1)):
            raise ValueError("review_model must use provider:model")
        return self


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


class StoryNovelCanonUpdateRequest(BaseModel):
    expected_plan_version: int = Field(..., ge=1)
    expected_canon_hash: str = Field(..., min_length=64, max_length=64)
    canon: StoryNovelCanon


class StoryNovelCanonUpdateResponse(BaseModel):
    revision: StoryNovelRevisionResponse
    canon_hash: str
    stale_from_position: Optional[int] = None


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
