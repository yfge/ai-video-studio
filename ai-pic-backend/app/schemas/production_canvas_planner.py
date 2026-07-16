from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProductionCanvasPlannerMode = Literal["autonomous", "deterministic_fallback"]


class ProductionCanvasPlannerStep(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    skill: str = Field(..., min_length=1, max_length=80)
    reason: str = Field(..., min_length=1, max_length=300)
    depends_on: list[str] = Field(default_factory=list, max_length=8)


class ProductionCanvasPlannerProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    objective: str = Field(..., min_length=1, max_length=500)
    steps: list[ProductionCanvasPlannerStep] = Field(..., min_length=1, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=8)


class ProductionCanvasPlannerEvidence(BaseModel):
    mode: ProductionCanvasPlannerMode
    version: str = "production_canvas.planner.v1"
    objective: str
    selected_skills: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    repair_count: int = Field(0, ge=0, le=1)
    fallback_reason: str | None = None
