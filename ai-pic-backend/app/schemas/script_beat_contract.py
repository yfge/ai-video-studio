from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCRIPT_BEAT_CONTRACT_VERSION = "script-beat-v1"

SceneRole = Literal["hook", "escalation", "payoff", "cliffhanger", "transition"]
BeatType = Literal[
    "hook",
    "setup",
    "conflict",
    "reveal",
    "payoff",
    "cliffhanger",
    "transition",
]


class ScriptBeatConflict(BaseModel):
    question: str = Field(..., min_length=1)
    stakes: str = Field(..., min_length=1)
    opposition: str = Field(..., min_length=1)
    turn: str | None = None


class ScriptBeatDialogueLine(BaseModel):
    character: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    emotion: str | None = None
    action: str | None = None


class ScriptBeatActionLine(BaseModel):
    content: str = Field(..., min_length=1)
    timing: str | None = None
    type: str | None = None


class ScriptBeat(BaseModel):
    order_index: int = Field(..., ge=1)
    beat_type: BeatType
    dramatic_purpose: str = Field(..., min_length=1)
    visible_event: str = Field(..., min_length=1)
    action_lines: list[ScriptBeatActionLine] = Field(default_factory=list)
    dialogue_lines: list[ScriptBeatDialogueLine] = Field(default_factory=list)
    duration_seconds: float | None = Field(None, ge=0)
    hook_tag: str | None = None
    payoff_tag: str | None = None
    cliffhanger_tag: str | None = None


class StructuredScriptScene(BaseModel):
    scene_number: int = Field(..., ge=1)
    slug_line: str = Field(..., min_length=1)
    location: str | None = None
    time_of_day: str | None = None
    estimated_duration_seconds: int | None = Field(None, ge=0)
    dramatic_role: SceneRole
    conflict: ScriptBeatConflict
    beats: list[ScriptBeat] = Field(..., min_length=1)


class StructuredScriptContract(BaseModel):
    model_config = ConfigDict(extra="allow")

    contract_version: Literal["script-beat-v1"] = SCRIPT_BEAT_CONTRACT_VERSION
    title: str | None = None
    logline: str | None = None
    scenes: list[StructuredScriptScene] = Field(..., min_length=1)
