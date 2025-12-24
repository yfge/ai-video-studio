"""
Pydantic schemas for the Timeline Agent.

Defines data structures for scene context, dialogue context,
timing decisions, and the complete agent state.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SceneContext(BaseModel):
    """Extracted context from scene for timing decisions."""

    scene_number: int = Field(..., description="Scene number in script")
    scene_id: int = Field(..., description="Database scene ID")
    mood: Optional[str] = Field(None, description="Dominant emotional mood")
    conflict_level: Literal["low", "medium", "high"] = Field(
        "medium", description="Narrative tension level"
    )
    pacing: Literal["slow", "medium", "fast"] = Field(
        "medium", description="Scene rhythm/tempo"
    )
    character_count: int = Field(1, ge=1, description="Number of characters")
    dialogue_count: int = Field(0, ge=0, description="Total dialogue lines")
    has_dramatic_question: bool = Field(
        False, description="Whether scene has dramatic tension"
    )


class DialogueContext(BaseModel):
    """Context for a single dialogue segment."""

    index: int = Field(..., ge=0, description="Position in dialogue sequence")
    speaker: str = Field(..., description="Character name")
    content: str = Field(..., description="Dialogue text")
    emotion: Optional[str] = Field(None, description="Tagged emotion")
    action: Optional[str] = Field(None, description="Inline stage direction")
    prev_emotion: Optional[str] = Field(None, description="Previous line emotion")
    next_emotion: Optional[str] = Field(None, description="Next line emotion")
    is_first: bool = Field(False, description="Is first dialogue in scene")
    is_last: bool = Field(False, description="Is last dialogue in scene")


class TimingDecision(BaseModel):
    """Single timing decision for a gap/pause."""

    segment_index: int = Field(..., ge=0, description="Dialogue segment index")
    gap_type: Literal[
        "pre_dialogue", "post_dialogue", "action_pause", "silence"
    ] = Field("post_dialogue", description="Type of gap")
    base_duration_ms: int = Field(
        300, ge=0, description="Baseline duration before adjustment"
    )
    adjusted_duration_ms: int = Field(
        300, ge=0, description="Final adjusted duration"
    )
    reasoning: str = Field("", description="Explanation for this decision")
    emotion_factor: float = Field(
        1.0, ge=0.0, le=3.0, description="Emotion-based multiplier"
    )
    pacing_factor: float = Field(
        1.0, ge=0.0, le=3.0, description="Pacing-based multiplier"
    )


class TimingPlan(BaseModel):
    """Complete timing plan for a scene."""

    scene_id: int = Field(..., description="Database scene ID")
    decisions: list[TimingDecision] = Field(
        default_factory=list, description="Ordered timing decisions"
    )
    total_gap_ms: int = Field(0, ge=0, description="Sum of all gap durations")
    avg_gap_ms: float = Field(0.0, ge=0.0, description="Average gap duration")
    rhythm_score: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Rhythm variety score (0=monotonous, 1=varied)",
    )
    reasoning_summary: str = Field("", description="Overall timing rationale")
    fallback_used: bool = Field(
        False, description="Whether fallback logic was used"
    )


class TimelineAgentState(BaseModel):
    """Complete agent state through the LangGraph pipeline."""

    # --- Input ---
    scene_context: Optional[SceneContext] = None
    dialogues: list[dict[str, Any]] = Field(default_factory=list)
    stage_directions: list[dict[str, Any]] = Field(default_factory=list)

    # --- Processing state ---
    dialogue_contexts: list[DialogueContext] = Field(default_factory=list)
    raw_llm_output: Optional[str] = None
    proposed_plan: Optional[TimingPlan] = None

    # --- Validation state ---
    validation_passed: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    repair_attempts: int = Field(0, ge=0, le=5)

    # --- Output ---
    final_plan: Optional[TimingPlan] = None

    # --- Trace ---
    reasoning: list[str] = Field(default_factory=list)
    provider_used: Optional[str] = None
    llm_model_used: Optional[str] = Field(None, alias="model_used")

    class Config:
        """Pydantic config."""

        extra = "allow"
        protected_namespaces = ()


# --- LLM Output Schema for structured generation ---
TIMING_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning_steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Step-by-step reasoning for timing decisions",
        },
        "timing_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment_index": {"type": "integer", "minimum": 0},
                    "gap_type": {
                        "type": "string",
                        "enum": [
                            "pre_dialogue",
                            "post_dialogue",
                            "action_pause",
                            "silence",
                        ],
                    },
                    "duration_ms": {"type": "integer", "minimum": 50, "maximum": 5000},
                    "reasoning": {"type": "string"},
                },
                "required": ["segment_index", "gap_type", "duration_ms"],
            },
        },
        "overall_rhythm_note": {"type": "string"},
    },
    "required": ["timing_decisions"],
}
