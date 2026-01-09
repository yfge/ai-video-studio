from datetime import datetime
from typing import Any, Dict, List, Optional

from app.schemas.user import UserSummary
from pydantic import BaseModel, Field, field_validator


# 故事概要相关schemas
class StoryCharacterBase(BaseModel):
    virtual_ip_id: int
    character_name: Optional[str] = None
    role_type: Optional[str] = Field(
        None, description="角色类型：protagonist, antagonist, supporting"
    )
    importance: int = Field(1, ge=1, le=5, description="重要度：1-5")
    personality: Optional[str] = None
    background: Optional[str] = None
    motivation: Optional[str] = None
    character_arc: Optional[str] = None
    relationships: Optional[Dict[str, Any]] = None


class StoryCharacterCreate(StoryCharacterBase):
    pass


class StoryCharacterUpdate(BaseModel):
    character_name: Optional[str] = None
    role_type: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    personality: Optional[str] = None
    background: Optional[str] = None
    motivation: Optional[str] = None
    character_arc: Optional[str] = None
    relationships: Optional[Dict[str, Any]] = None


class StoryCharacterResponse(StoryCharacterBase):
    id: int
    story_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryBase(BaseModel):
    title: str = Field(..., max_length=255)
    story_format: str = Field(
        "short_drama",
        description="故事形态：short_drama（短剧）/ tv_series（电视剧/网剧）/ film（电影）",
    )
    genre: str = Field(..., max_length=50)
    theme: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1)

    premise: Optional[str] = None
    synopsis: Optional[str] = None
    main_conflict: Optional[str] = None
    resolution: Optional[str] = None

    main_characters: Optional[List[Dict[str, Any]]] = None
    character_relationships: Optional[Dict[str, Any]] = None

    setting_time: Optional[str] = Field(None, max_length=100)
    setting_location: Optional[str] = Field(None, max_length=255)
    world_building: Optional[str] = None

    status: str = Field("draft", description="状态：draft, approved, published")
    is_public: bool = False
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None

    @field_validator("story_format", mode="before")
    @classmethod
    def _coerce_story_format(cls, value: Any) -> str:
        if value is None:
            return "short_drama"
        if isinstance(value, str) and not value.strip():
            return "short_drama"
        return str(value)


class StoryCreate(StoryBase):
    characters: Optional[List[StoryCharacterCreate]] = None


class StoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    story_format: Optional[str] = Field(
        None,
        description="故事形态：short_drama（短剧）/ tv_series（电视剧/网剧）/ film（电影）",
    )
    genre: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1)

    premise: Optional[str] = None
    synopsis: Optional[str] = None
    main_conflict: Optional[str] = None
    resolution: Optional[str] = None

    main_characters: Optional[List[Dict[str, Any]]] = None
    character_relationships: Optional[Dict[str, Any]] = None

    setting_time: Optional[str] = Field(None, max_length=100)
    setting_location: Optional[str] = Field(None, max_length=255)
    world_building: Optional[str] = None

    status: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class StoryResponse(StoryBase):
    id: int
    business_id: str
    generation_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    creator: Optional[UserSummary] = Field(None, validation_alias="owner")
    created_at: datetime
    updated_at: datetime

    story_characters: Optional[List[StoryCharacterResponse]] = None

    class Config:
        from_attributes = True


# 剧集相关schemas
class EpisodeBase(BaseModel):
    episode_number: int = Field(..., ge=1)
    title: str = Field(..., max_length=255)
    summary: Optional[str] = None
    plot_points: Optional[List[Dict[str, Any]]] = None
    character_arcs: Optional[Dict[str, Any]] = None
    conflicts: Optional[List[Dict[str, Any]]] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    scene_count: Optional[int] = Field(None, ge=1)
    status: str = Field("draft", description="状态：draft, approved, published")
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class EpisodeCreate(EpisodeBase):
    story_id: int


class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    plot_points: Optional[List[Dict[str, Any]]] = None
    character_arcs: Optional[Dict[str, Any]] = None
    conflicts: Optional[List[Dict[str, Any]]] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    scene_count: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class EpisodeResponse(EpisodeBase):
    id: int
    business_id: str
    story_id: int
    story_business_id: Optional[str] = None
    generation_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 剧本相关schemas
class ScriptBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: Optional[str] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    dialogues: Optional[List[Dict[str, Any]]] = None
    stage_directions: Optional[List[Dict[str, Any]]] = None
    format_type: str = Field("screenplay", max_length=50)
    language: str = Field("zh-CN", max_length=10)
    status: str = Field("draft", description="状态：draft, approved, published")
    version: str = Field("1.0", max_length=20)
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ScriptCreate(ScriptBase):
    episode_id: int


class ScriptUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    dialogues: Optional[List[Dict[str, Any]]] = None
    stage_directions: Optional[List[Dict[str, Any]]] = None
    format_type: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ScriptResponse(ScriptBase):
    id: int
    business_id: str
    episode_id: int
    episode_business_id: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    generation_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 模板相关schemas
class ScriptTemplateBase(BaseModel):
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    template_content: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_public: bool = False


class ScriptTemplateCreate(ScriptTemplateBase):
    pass


class ScriptTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    template_content: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class ScriptTemplateResponse(ScriptTemplateBase):
    id: int
    usage_count: int
    rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
