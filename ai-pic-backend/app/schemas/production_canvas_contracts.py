from __future__ import annotations

from datetime import datetime
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
    "text", "contract", "image", "video", "audio", "entity_ref", "execution_ref"
]
CanvasBindingType = Literal["value", "selected_output"]
ReuseTargetKind = Literal["api", "repository", "service", "worker", "artifact"]
CanvasSectionScope = Literal["episode", "scene"]


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


class ProductionCanvasSavedPort(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    type: CanvasPortType
    required: bool = False
    multiple: bool = False


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
    definition_version: int = Field(1, ge=1)
    input_ports: list[ProductionCanvasSavedPort] = Field(default_factory=list)
    output_ports: list[ProductionCanvasSavedPort] = Field(default_factory=list)


class ProductionCanvasViewport(BaseModel):
    x: float
    y: float
    zoom: float


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
    execution_input_fingerprint: str | None = Field(None, max_length=64)
    selected_output_id: int | None = Field(None, ge=1)
    selected_output_url: str | None = None
    selected_output_reviewed_by: int | None = Field(None, ge=1)
    selected_output_reviewed_at: datetime | None = None
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


class ProductionCanvasSavedSection(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=120)
    scope: CanvasSectionScope
    node_ids: list[str] = Field(default_factory=list, max_length=200)
    x: float
    y: float
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    collapsed: bool = False


class ProductionCanvasSavedState(BaseModel):
    graph_version: Literal[1, 2] = 1
    resolved_context_revision: int = Field(0, ge=0)
    nodes: list[ProductionCanvasSavedNode] = Field(default_factory=list)
    edges: list[ProductionCanvasSavedEdge] = Field(default_factory=list)
    sections: list[ProductionCanvasSavedSection] = Field(default_factory=list)
    viewport: ProductionCanvasViewport
    selected_node_id: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def validate_graph(self):
        from app.services.production_canvas.graph_validation import validate_saved_graph

        validate_saved_graph(self)
        return self
