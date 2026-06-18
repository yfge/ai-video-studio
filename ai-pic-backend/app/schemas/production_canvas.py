from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


CanvasNodeStatus = Literal["ready", "running", "review", "blocked"]
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


class ProductionCanvasPlanResponse(BaseModel):
    prompt: str
    run_id: str | None = None
    task_id: int | None = None
    skill_manifest: ProductionCanvasSkillManifest
    selected_assets: ProductionCanvasSelectedAssets
    skill_results: list[ProductionCanvasSkillResult] = Field(default_factory=list)
    nodes: list[ProductionCanvasPlanNode]


class ProductionCanvasSkillExecuteResponse(BaseModel):
    skill_result: ProductionCanvasSkillResult
    task_id: int | None = None
    task_status: str | None = None
