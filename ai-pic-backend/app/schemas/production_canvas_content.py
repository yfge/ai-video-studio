from __future__ import annotations

from typing import Literal

from app.schemas.production_canvas_brief import ProductionCanvasProductionBrief
from pydantic import BaseModel, Field


class ProductionCanvasCharacterPlan(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=1000)
    season_arc: str | None = Field(None, max_length=1500)
    continuity_anchors: list[str] = Field(default_factory=list, max_length=12)


class ProductionCanvasEnvironmentPlan(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    purpose: str = Field(..., min_length=1, max_length=500)
    reuse_across_episodes: bool = True


class ProductionCanvasEpisodePlan(BaseModel):
    episode_number: int = Field(..., ge=1, le=1000)
    title: str = Field(..., min_length=1, max_length=255)
    logline: str = Field(..., min_length=1, max_length=1000)
    beats: list[str] = Field(..., min_length=3, max_length=12)
    payoff: str = Field(..., min_length=1, max_length=1000)
    cliffhanger: str = Field(..., min_length=1, max_length=1000)
    continuity_handoff: list[str] = Field(default_factory=list, max_length=12)


class ProductionCanvasContentPlan(BaseModel):
    version: str = "content_plan.v1"
    title: str = Field(..., min_length=1, max_length=255)
    premise: str = Field(..., min_length=1, max_length=2000)
    synopsis: str = Field(..., min_length=1, max_length=5000)
    main_conflict: str = Field(..., min_length=1, max_length=2000)
    theme: str | None = Field(None, max_length=500)
    characters: list[ProductionCanvasCharacterPlan] = Field(
        default_factory=list,
        max_length=20,
    )
    environments: list[ProductionCanvasEnvironmentPlan] = Field(
        default_factory=list,
        max_length=20,
    )
    season_arc: str = Field(..., min_length=1, max_length=5000)
    recurring_engine: str = Field(..., min_length=1, max_length=2000)
    episodes: list[ProductionCanvasEpisodePlan] = Field(
        default_factory=list,
        max_length=100,
    )
    continuity_rules: list[str] = Field(default_factory=list, max_length=30)
    future_threads: list[str] = Field(default_factory=list, max_length=30)


class ProductionCanvasAssetAssociation(BaseModel):
    kind: Literal["virtual_ip", "environment"]
    requested_name: str | None = None
    decision: Literal[
        "reused",
        "created",
        "ambiguous",
        "missing",
        "not_required",
    ]
    asset_id: int | None = None
    asset_name: str | None = None
    candidate_ids: list[int] = Field(default_factory=list)
    reason: str


class ProductionCanvasPlanningDraft(BaseModel):
    brief: ProductionCanvasProductionBrief
    content_plan: ProductionCanvasContentPlan


class ProductionCanvasProductionContext(BaseModel):
    version: str = "production_context.v1"
    brief: ProductionCanvasProductionBrief
    content_plan: ProductionCanvasContentPlan
    asset_associations: list[ProductionCanvasAssetAssociation] = Field(
        default_factory=list
    )
    selected_asset_ids: dict[str, list[int]] = Field(default_factory=dict)
    created_story_ids: list[int] = Field(default_factory=list)
    created_episode_ids: list[int] = Field(default_factory=list)
