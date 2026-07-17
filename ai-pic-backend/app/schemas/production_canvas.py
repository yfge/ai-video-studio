from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from app.schemas.production_canvas_brief import ProductionCanvasBriefOverrides
from app.schemas.production_canvas_collaboration import CanvasAccessRole
from app.schemas.production_canvas_content import ProductionCanvasProductionContext
from app.schemas.production_canvas_contracts import (
    CanvasBindingType,
    CanvasNodeKind,
    CanvasNodeStatus,
    CanvasPortType,
    CanvasSectionScope,
    ProductionCanvasAssetSummary,
    ProductionCanvasPlanNode,
    ProductionCanvasSavedEdge,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedPort,
    ProductionCanvasSavedSection,
    ProductionCanvasSavedState,
    ProductionCanvasSelectedAssets,
    ProductionCanvasSkillDefinition,
    ProductionCanvasSkillManifest,
    ProductionCanvasSkillResult,
    ProductionCanvasSkillReuseTarget,
    ProductionCanvasViewport,
    ReuseTargetKind,
)
from app.schemas.production_canvas_planner import ProductionCanvasPlannerEvidence
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CanvasBindingType",
    "CanvasNodeKind",
    "CanvasNodeStatus",
    "CanvasPortType",
    "CanvasSectionScope",
    "ProductionCanvasAssetSummary",
    "ProductionCanvasSavedNode",
    "ProductionCanvasSavedPort",
    "ProductionCanvasSavedSection",
    "ProductionCanvasSkillDefinition",
    "ProductionCanvasSkillReuseTarget",
    "ProductionCanvasViewport",
    "ReuseTargetKind",
]


class ProductionCanvasResolvedContext(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    virtual_ip_id: int | None = Field(None, ge=1)
    environment_id: int | None = Field(None, ge=1)
    story_id: int | None = Field(None, ge=1)
    episode_id: int | None = Field(None, ge=1)
    script_id: int | None = Field(None, ge=1)
    timeline_id: int | None = Field(None, ge=1)
    timeline_version: int | None = Field(None, ge=1)
    clip_id: str | None = Field(None, min_length=1, max_length=128)
    task_id: int | None = Field(None, ge=1)


class ProductionCanvasPlanRequest(ProductionCanvasResolvedContext):
    prompt: str = Field(..., min_length=1, max_length=2000)
    planning_mode: Literal["series", "single_video"] = "series"
    brief_overrides: ProductionCanvasBriefOverrides = Field(
        default_factory=ProductionCanvasBriefOverrides
    )
    clarification_answers: dict[str, str] = Field(default_factory=dict)


class ProductionCanvasSkillExecuteRequest(ProductionCanvasPlanRequest):
    skill: str = Field(..., min_length=1, max_length=80)
    run_id: str | None = Field(None, max_length=32)
    node_id: str | None = Field(None, max_length=120)
    execution_scope: Literal["node", "downstream"] = "node"
    reference_artifacts: list[str] = Field(default_factory=list, max_length=20)
    start_frame_url: str | None = None
    frame_indexes: list[int] | None = None
    model: str | None = Field(None, max_length=120)
    aspect_ratio: str | None = Field(None, max_length=16)
    require_reference_images: bool | None = None
    duration: float | None = None
    fps: int | None = None
    resolution: str | None = Field(None, max_length=32)
    ratio: str | None = Field(None, max_length=16)
    camera_fixed: bool | None = None
    branch_parent_candidate_id: int | None = Field(None, ge=1)
    branch_instruction: str | None = Field(None, max_length=1000)
    production_context: ProductionCanvasProductionContext | None = None


class ProductionCanvasPlanResponse(BaseModel):
    prompt: str
    run_id: str | None = None
    task_id: int | None = None
    resolved_context: ProductionCanvasResolvedContext = Field(
        default_factory=ProductionCanvasResolvedContext
    )
    skill_manifest: ProductionCanvasSkillManifest
    selected_assets: ProductionCanvasSelectedAssets
    production_context: ProductionCanvasProductionContext | None = None
    skill_results: list[ProductionCanvasSkillResult] = Field(default_factory=list)
    nodes: list[ProductionCanvasPlanNode]
    edges: list[ProductionCanvasSavedEdge] = Field(default_factory=list)
    planner: ProductionCanvasPlannerEvidence


class ProductionCanvasExecutionAttempt(BaseModel):
    attempt_id: int = Field(..., ge=1)
    node_id: str
    skill: str
    status: CanvasNodeStatus
    definition_version: int = Field(..., ge=1)
    definition_mode: Literal["current", "original"] = "current"
    task_id: int | None = None
    task_status: str | None = None
    created_at: datetime


class ProductionCanvasRunResponse(ProductionCanvasPlanResponse):
    access_role: CanvasAccessRole = "owner"
    saved_state: ProductionCanvasSavedState | None = None
    execution_attempts: list[ProductionCanvasExecutionAttempt] = Field(
        default_factory=list
    )


class ProductionCanvasNodeExecution(BaseModel):
    skill_result: ProductionCanvasSkillResult
    resolved_context: ProductionCanvasResolvedContext = Field(
        default_factory=ProductionCanvasResolvedContext
    )
    task_id: int | None = None
    task_status: str | None = None
    node_id: str | None = None
    resolved_inputs: dict[str, Any] = Field(default_factory=dict)
    input_fingerprint: str | None = None
    resolved_context_revision: int = Field(0, ge=0)


class ProductionCanvasSkillExecuteResponse(ProductionCanvasNodeExecution):
    execution_order: list[str] = Field(default_factory=list)
    executions: list[ProductionCanvasNodeExecution] = Field(default_factory=list)


class ProductionCanvasRunActionRequest(BaseModel):
    action: Literal["run_ready", "resume", "cancel", "retry"]
    node_id: str | None = Field(None, max_length=120)
    definition_mode: Literal["current", "original"] = "current"


class ProductionCanvasRunActionResponse(BaseModel):
    action: Literal["run_ready", "resume", "cancel", "retry"]
    definition_mode: Literal["current", "original"] = "current"
    run: ProductionCanvasRunResponse
    executions: list[ProductionCanvasNodeExecution] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)
    skipped_node_ids: list[str] = Field(default_factory=list)
    cancelled_task_ids: list[int] = Field(default_factory=list)


class ProductionCanvasGraphNodeState(BaseModel):
    node_id: str
    status: CanvasNodeStatus
    missing_inputs: list[str] = Field(default_factory=list)


class ProductionCanvasGraphEvaluation(BaseModel):
    graph_version: int
    node_states: list[ProductionCanvasGraphNodeState] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)
