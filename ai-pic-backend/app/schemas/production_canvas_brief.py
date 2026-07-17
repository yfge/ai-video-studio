from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProductionCanvasIntentKind = Literal[
    "story_series",
    "single_video",
    "episode_continuation",
    "advertisement",
    "explainer",
    "product_demo",
    "other",
]
ProductionCanvasAssetPolicy = Literal[
    "reuse_preferred",
    "reuse_only",
    "create_if_missing",
    "create_new",
    "ask_if_ambiguous",
]
ProductionCanvasModelStatus = Literal[
    "requested",
    "auto_selected",
    "pipeline_default",
    "unavailable",
]
ProductionCanvasInterpretationStatus = Literal[
    "model_parsed",
    "deterministic_compatibility",
    "failed",
]


class ProductionCanvasClarificationOption(BaseModel):
    label: str = Field(..., min_length=1, max_length=120)
    value: str = Field(..., min_length=1, max_length=200)


class ProductionCanvasClarification(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=1, max_length=100)
    field: str = Field(..., min_length=1, max_length=120)
    question: str = Field(..., min_length=1, max_length=500)
    reason: str = Field(..., min_length=1, max_length=500)
    required: bool = True
    options: list[ProductionCanvasClarificationOption] = Field(
        default_factory=list,
        max_length=20,
    )
    answer: str | None = Field(None, max_length=1000)


class ProductionCanvasBriefConflict(BaseModel):
    field: str
    prompt_value: str | None = None
    authoritative_value: str | None = None
    resolution: str
    reason: str


class ProductionCanvasCreativeIntent(BaseModel):
    kind: ProductionCanvasIntentKind = "other"
    objective: str
    narrative_seed: str
    genre: str | None = None
    tone: list[str] = Field(default_factory=list, max_length=12)
    target_audience: str | None = None
    language: str = "zh-CN"
    must_include: list[str] = Field(default_factory=list, max_length=30)
    must_avoid: list[str] = Field(default_factory=list, max_length=30)


class ProductionCanvasVideoSpec(BaseModel):
    duration_seconds: int | None = Field(None, ge=1, le=7200)
    episode_count: int | None = Field(None, ge=1, le=100)
    focus_episode_number: int | None = Field(None, ge=1, le=1000)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] | None = None
    resolution: str | None = Field(None, max_length=32)
    fps: int | None = Field(None, ge=1, le=120)
    visual_style: list[str] = Field(default_factory=list, max_length=12)


class ProductionCanvasModelChoice(BaseModel):
    requested: str | None = Field(None, max_length=160)
    selected: str | None = Field(None, max_length=160)
    provider: str | None = Field(None, max_length=80)
    status: ProductionCanvasModelStatus = "pipeline_default"
    reason: str = "沿用现有生产链默认模型。"


class ProductionCanvasModelPlan(BaseModel):
    text: ProductionCanvasModelChoice = Field(
        default_factory=ProductionCanvasModelChoice
    )
    image: ProductionCanvasModelChoice = Field(
        default_factory=ProductionCanvasModelChoice
    )
    video: ProductionCanvasModelChoice = Field(
        default_factory=ProductionCanvasModelChoice
    )


class ProductionCanvasAssetIntent(BaseModel):
    virtual_ip_name: str | None = Field(None, max_length=120)
    virtual_ip_description: str | None = Field(None, max_length=1000)
    environment_names: list[str] = Field(default_factory=list, max_length=12)
    asset_policy: ProductionCanvasAssetPolicy = "reuse_preferred"


class ProductionCanvasBriefOverrides(BaseModel):
    title: str | None = Field(None, max_length=255)
    duration_seconds: int | None = Field(None, ge=1, le=7200)
    episode_count: int | None = Field(None, ge=1, le=100)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] | None = None
    resolution: str | None = Field(None, max_length=32)
    fps: int | None = Field(None, ge=1, le=120)
    text_model: str | None = Field(None, max_length=160)
    image_model: str | None = Field(None, max_length=160)
    video_model: str | None = Field(None, max_length=160)
    visual_style: str | None = Field(None, max_length=255)


class ProductionCanvasProductionBrief(BaseModel):
    version: str = "production_brief.v1"
    source_prompt: str
    interpretation_status: ProductionCanvasInterpretationStatus = "model_parsed"
    interpretation_warnings: list[str] = Field(default_factory=list, max_length=8)
    intent: ProductionCanvasCreativeIntent
    video_spec: ProductionCanvasVideoSpec = Field(
        default_factory=ProductionCanvasVideoSpec
    )
    models: ProductionCanvasModelPlan = Field(default_factory=ProductionCanvasModelPlan)
    assets: ProductionCanvasAssetIntent = Field(
        default_factory=ProductionCanvasAssetIntent
    )
    conflicts: list[ProductionCanvasBriefConflict] = Field(
        default_factory=list,
        max_length=20,
    )
    clarifications: list[ProductionCanvasClarification] = Field(
        default_factory=list,
        max_length=10,
    )
    ready_for_execution: bool = True
