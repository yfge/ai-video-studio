from typing import List, Literal, Optional

from app.schemas.generation import AdSnippet, HookPlan
from pydantic import BaseModel, Field


class StoryGenerationRequest(BaseModel):
    # 基本信息
    title: str = Field(..., max_length=255)
    story_format: Literal["short_drama", "tv_series", "film"] = Field(
        "short_drama",
        description="故事形态：short_drama（短剧）/ tv_series（电视剧/网剧）/ film（电影）",
    )
    default_aspect_ratio: Literal["9:16", "16:9"] = Field(
        "9:16", description="默认画幅：9:16/16:9"
    )
    genre: str = Field(..., max_length=50)
    market_region: Optional[str] = Field(
        None, max_length=50, description="目标市场/地区"
    )
    micro_genre: Optional[str] = Field(
        None, max_length=80, description="微类型/细分题材"
    )
    pacing_template: Optional[str] = Field(
        None,
        max_length=80,
        description="节奏模板（前端可用于自动填充 hook_plan 等字段）",
    )
    hook_plan: Optional[HookPlan] = Field(
        None, description="爽点/钩子节奏规划（可选预设）"
    )
    twist_density: Optional[str] = Field(None, description="反转密度目标（可选预设）")
    cliffhanger_plan: Optional[List[str]] = Field(
        None, description="悬念/卡点规划（可选预设）"
    )
    ad_snippets: Optional[List[AdSnippet]] = Field(
        None, description="投流素材建议（可选预设）"
    )
    theme: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1)

    # 角色信息
    character_ids: List[int] = Field(
        ..., min_items=1, description="参与的虚拟IP ID列表"
    )

    # 设定信息
    setting_time: Optional[str] = Field(None, max_length=100)
    setting_location: Optional[str] = Field(None, max_length=255)
    world_building: Optional[str] = None

    # 生成参数
    additional_requirements: Optional[str] = None
    style_preferences: Optional[List[str]] = None
    content_restrictions: Optional[List[str]] = None

    # AI参数
    model: Optional[str] = Field(
        None, description="指定文本生成模型，如 openai:gpt-4o-mini"
    )
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.5, description="创造性温度")

    # 元数据
    tags: Optional[List[str]] = None


class EpisodeGenerationRequest(BaseModel):
    story_id: int
    episode_count: int = Field(..., ge=1, le=50, description="要生成的剧集数量")
    episode_duration: Optional[int] = Field(None, ge=1, description="每集时长（分钟）")

    # 市场与微类型
    market_region: Optional[str] = Field(
        None, max_length=50, description="目标市场/地区"
    )
    micro_genre: Optional[str] = Field(
        None, max_length=80, description="微类型/细分题材"
    )
    pacing_template: Optional[str] = Field(
        None,
        max_length=80,
        description="节奏模板（前端可用于自动填充 hook_plan 等字段）",
    )
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")

    # 生成参数
    focus_characters: Optional[List[int]] = None
    plot_complexity: str = Field(
        "medium", description="情节复杂度：simple, medium, complex"
    )
    pacing: str = Field("medium", description="节奏：slow, medium, fast")

    # 额外要求
    additional_requirements: Optional[str] = None
    style_preferences: Optional[List[str]] = None

    # AI参数
    model: Optional[str] = Field(
        None, description="指定文本生成模型，如 openai:gpt-4o-mini"
    )
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.5, description="创造性温度")


class ScriptGenerationRequest(BaseModel):
    episode_id: int
    format_type: str = Field("screenplay", description="剧本格式")
    language: str = Field("zh-CN", description="语言")

    # 市场与微类型
    market_region: Optional[str] = Field(
        None, max_length=50, description="目标市场/地区"
    )
    micro_genre: Optional[str] = Field(
        None, max_length=80, description="微类型/细分题材"
    )
    pacing_template: Optional[str] = Field(
        None,
        max_length=80,
        description="节奏模板（前端可用于自动填充 hook_plan 等字段）",
    )
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")

    # 生成参数
    dialogue_style: str = Field(
        "natural", description="对话风格：formal, natural, casual"
    )
    scene_detail_level: str = Field(
        "medium", description="场景描述详细程度：minimal, medium, detailed"
    )

    # 额外要求
    additional_requirements: Optional[str] = None
    style_preferences: Optional[List[str]] = None

    # AI参数
    model: Optional[str] = Field(
        None, description="指定文本生成模型，如 openai:gpt-4o-mini"
    )
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.5, description="创造性温度")


class StoryNovelExportRequest(BaseModel):
    """将 Story 扩写为长文本小说（默认知乎体）。"""

    style: Literal["zhihu"] = Field("zhihu", description="输出风格：zhihu（知乎体）")
    target_words: int = Field(
        20000, ge=10000, le=30000, description="目标字数（1-3万字）"
    )
    chapter_count: Optional[int] = Field(
        None, ge=3, le=24, description="章节数（可选，默认按目标字数自动估算）"
    )

    model: Optional[str] = Field(
        None, description="指定文本生成模型，如 openai:gpt-4o-mini"
    )
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.5, description="创造性温度")
