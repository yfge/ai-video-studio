from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.schemas.script_beat_contract import BeatType, SceneRole

_SCENE_ROLES = set(SceneRole.__args__)
_BEAT_TYPES = set(BeatType.__args__)
_SCENE_ROLE_ALIASES = {
    "conflict": "escalation",
    "conflict_escalation": "escalation",
    "conflict_ladder": "escalation",
    "crisis": "escalation",
    "discovery": "escalation",
    "investigation": "escalation",
    "progression": "escalation",
    "progressive": "escalation",
    "reveal": "escalation",
    "revelation": "escalation",
    "rising": "escalation",
    "rising_action": "escalation",
    "resolution": "payoff",
    "turning_point": "escalation",
    "twist": "escalation",
    "button": "cliffhanger",
    "final_button": "cliffhanger",
}
_BEAT_TYPE_ALIASES = {
    "action": "transition",
    "beat": "setup",
    "choice": "transition",
    "choice_point": "transition",
    "climax": "payoff",
    "confirmation": "reveal",
    "confrontation": "conflict",
    "crisis": "conflict",
    "conflict_ladder": "conflict",
    "decision": "transition",
    "discovery": "reveal",
    "evidence": "reveal",
    "escalation": "conflict",
    "final_button": "cliffhanger",
    "investigation": "setup",
    "jolt": "reveal",
    "proof": "reveal",
    "progression": "conflict",
    "progressive": "conflict",
    "reaction": "transition",
    "resolution": "payoff",
    "reversal": "reveal",
    "revelation": "reveal",
    "rising_action": "conflict",
    "spike": "payoff",
    "threat": "conflict",
    "turn": "reveal",
    "twist": "reveal",
    "verification": "reveal",
    "button": "cliffhanger",
}


def canonicalize_contract_enums(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(payload)
    scenes = normalized.get("scenes")
    if not isinstance(scenes, list):
        return normalized

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        if "dramatic_role" in scene:
            scene["dramatic_role"] = _scene_role_alias(scene["dramatic_role"])
        _canonicalize_scene_beats(scene)
    return normalized


def _canonicalize_scene_beats(scene: dict[str, Any]) -> None:
    beats = scene.get("beats")
    if not isinstance(beats, list):
        return
    for beat in beats:
        if isinstance(beat, dict) and "beat_type" in beat:
            beat["beat_type"] = _beat_type_alias(beat["beat_type"])


def _scene_role_alias(value: Any) -> Any:
    raw = str(value or "").strip()
    canonical = raw.lower()
    if canonical in _SCENE_ROLES:
        return canonical
    if canonical in _SCENE_ROLE_ALIASES:
        return _SCENE_ROLE_ALIASES[canonical]
    return "escalation" if raw else value


def _beat_type_alias(value: Any) -> Any:
    raw = str(value or "").strip()
    canonical = raw.lower()
    if canonical in _BEAT_TYPES:
        return canonical
    if canonical in _BEAT_TYPE_ALIASES:
        return _BEAT_TYPE_ALIASES[canonical]
    return "conflict" if raw else value
