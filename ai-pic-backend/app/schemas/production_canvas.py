from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CanvasNodeKind = Literal["pipeline", "note", "skill_result"]
CanvasNodeStatus = Literal[
    "draft",
    "ready",
    "queued",
    "running",
    "review",
    "approved",
    "stale",
    "failed",
    "cancelled",
    "blocked",
]
CanvasPortType = Literal[
    "text", "image", "video", "audio", "entity_ref", "execution_ref"
]
CanvasBindingType = Literal["value", "selected_output"]
ReuseTargetKind = Literal["api", "repository", "service", "worker", "artifact"]


class ProductionCanvasPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    virtual_ip_id: int | None = None
    environment_id: int | None = None
    episode_id: int | None = None
    script_id: int | None = None
    task_id: int | None = None


class ProductionCanvasSkillExecuteRequest(ProductionCanvasPlanRequest):
    skill: str = Field(..., min_length=1, max_length=80)
    run_id: str | None = Field(None, max_length=32)
    node_id: str | None = Field(None, max_length=120)
    execution_scope: Literal["node", "downstream"] = "node"
    reference_artifacts: list[str] = Field(default_factory=list, max_length=20)
    frame_indexes: list[int] | None = None
    model: str | None = Field(None, max_length=120)
    aspect_ratio: str | None = Field(None, max_length=16)
    require_reference_images: bool | None = None
    duration: float | None = None
    fps: int | None = None
    resolution: str | None = Field(None, max_length=32)
    ratio: str | None = Field(None, max_length=16)
    camera_fixed: bool | None = None


class ProductionCanvasAssetSummary(BaseModel):
    id: int
    business_id: str | None = None
    name: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    reference_images: list[str] = Field(default_factory=list)


class ProductionCanvasSelectedAssets(BaseModel):
    virtual_ips: list[ProductionCanvasAssetSummary] = Field(default_factory=list)
    environments: list[ProductionCanvasAssetSummary] = Field(default_factory=list)


class ProductionCanvasSkillReuseTarget(BaseModel):
    kind: ReuseTargetKind
    label: str
    target: str
    description: str | None = None


class ProductionCanvasSkillDefinition(BaseModel):
    id: str
    label: str
    description: str
    reuse_targets: list[ProductionCanvasSkillReuseTarget] = Field(default_factory=list)


class ProductionCanvasSkillResult(BaseModel):
    skill: str
    label: str
    status: CanvasNodeStatus
    title: str
    detail: str
    outputs: dict[str, Any] = Field(default_factory=dict)
    reuse_targets: list[ProductionCanvasSkillReuseTarget] = Field(default_factory=list)


class ProductionCanvasSkillManifest(BaseModel):
    version: str
    entry_skill: str
    skills: list[ProductionCanvasSkillDefinition]
    reuse_policy: str


class ProductionCanvasPlanNode(BaseModel):
    id: str
    label: str
    title: str
    status: CanvasNodeStatus
    x: int
    y: int
    width: int
    kind: str = "skill_result"
    skill: str
    detail: str
    outputs: dict[str, Any] = Field(default_factory=dict)
    reuse_targets: list[ProductionCanvasSkillReuseTarget] = Field(default_factory=list)
    action_href: str | None = None
    action_label: str | None = None


class ProductionCanvasViewport(BaseModel):
    x: float
    y: float
    zoom: float


class ProductionCanvasSavedPort(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    type: CanvasPortType
    required: bool = False
    multiple: bool = False


class ProductionCanvasSavedNode(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    label: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=255)
    status: CanvasNodeStatus
    x: float
    y: float
    width: float
    height: float | None = None
    kind: CanvasNodeKind | None = None
    skill: str | None = Field(None, max_length=80)
    detail: str | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    reuse_targets: list[ProductionCanvasSkillReuseTarget] = Field(default_factory=list)
    action_href: str | None = None
    action_label: str | None = None
    definition_version: int = Field(1, ge=1)
    input_ports: list[ProductionCanvasSavedPort] = Field(default_factory=list)
    output_ports: list[ProductionCanvasSavedPort] = Field(default_factory=list)


class ProductionCanvasSavedEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(..., alias="from", min_length=1, max_length=120)
    to_node: str = Field(..., alias="to", min_length=1, max_length=120)
    edge_id: str | None = Field(None, min_length=1, max_length=160)
    from_port: str | None = Field(None, min_length=1, max_length=80)
    to_port: str | None = Field(None, min_length=1, max_length=80)
    binding_type: CanvasBindingType | None = None
    required: bool = True
    binding_order: int | None = Field(None, ge=0)


class ProductionCanvasSavedState(BaseModel):
    graph_version: Literal[1, 2] = 1
    nodes: list[ProductionCanvasSavedNode] = Field(default_factory=list)
    edges: list[ProductionCanvasSavedEdge] = Field(default_factory=list)
    viewport: ProductionCanvasViewport
    selected_node_id: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def validate_graph(self):
        from app.services.production_canvas.graph_validation import validate_saved_graph

        validate_saved_graph(self)
        return self


class ProductionCanvasPlanResponse(BaseModel):
    prompt: str
    run_id: str | None = None
    task_id: int | None = None
    skill_manifest: ProductionCanvasSkillManifest
    selected_assets: ProductionCanvasSelectedAssets
    skill_results: list[ProductionCanvasSkillResult] = Field(default_factory=list)
    nodes: list[ProductionCanvasPlanNode]


class ProductionCanvasRunResponse(ProductionCanvasPlanResponse):
    saved_state: ProductionCanvasSavedState | None = None


class ProductionCanvasNodeExecution(BaseModel):
    skill_result: ProductionCanvasSkillResult
    task_id: int | None = None
    task_status: str | None = None
    node_id: str | None = None
    resolved_inputs: dict[str, Any] = Field(default_factory=dict)


class ProductionCanvasSkillExecuteResponse(ProductionCanvasNodeExecution):
    execution_order: list[str] = Field(default_factory=list)
    executions: list[ProductionCanvasNodeExecution] = Field(default_factory=list)


class ProductionCanvasGraphNodeState(BaseModel):
    node_id: str
    status: CanvasNodeStatus
    missing_inputs: list[str] = Field(default_factory=list)


class ProductionCanvasGraphEvaluation(BaseModel):
    graph_version: int
    node_states: list[ProductionCanvasGraphNodeState] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)
