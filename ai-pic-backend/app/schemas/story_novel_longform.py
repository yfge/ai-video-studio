"""Structured contracts for outline-driven long-form novel generation."""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class StoryNovelChapterPlan(BaseModel):
    position: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    key_events: list[str] = Field(..., min_length=1)
    character_focus: list[str] = Field(default_factory=list)
    open_threads: list[str] = Field(default_factory=list)
    end_state: str = Field(..., min_length=1)
    target_chars: int = Field(..., ge=3000, le=5000)


class StoryNovelGenerationPlan(BaseModel):
    chapters: list[StoryNovelChapterPlan] = Field(..., min_length=1)

    @model_validator(mode="after")
    def require_contiguous_positions(self):
        positions = [item.position for item in self.chapters]
        if positions != list(range(1, len(self.chapters) + 1)):
            raise ValueError("chapter positions must start at 1 and be contiguous")
        return self


class StoryNovelPlotDelta(BaseModel):
    key_events: list[str] = Field(default_factory=list)
    unresolved_threads: list[str] = Field(default_factory=list)
    resolved_threads: list[str] = Field(default_factory=list)
    character_states: dict[str, Any] = Field(default_factory=dict)


class StoryNovelChapterGeneration(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content_text: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    cliffhanger: str | None = None
    plot_delta: StoryNovelPlotDelta = Field(default_factory=StoryNovelPlotDelta)
