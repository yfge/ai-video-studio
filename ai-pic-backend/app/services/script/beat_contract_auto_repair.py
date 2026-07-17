from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.script.beat_contract_auto_repair_conflict import repair_scene_conflict
from app.services.script.beat_contract_auto_repair_payoff import ensure_contract_payoff
from app.services.script.beat_contract_auto_repair_polish import (
    align_scene_durations,
    harden_final_cliffhanger,
    harden_opening_hook,
    repair_beats,
)
from app.services.script.beat_contract_dialogue_repair import (
    dedupe_progression,
    shorten_dialogue_lines,
)
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
from app.services.script_quality_gate_repair_guard import (
    repair_preserves_script_structure,
)


def auto_repair_script_beat_contract(
    content: dict[str, Any],
    *,
    format_type: str = "screenplay",
    language: str = "zh-CN",
    episode_number: int | None = None,
    template_style: str | None = "commercial_vertical_drama",
    target_chars_per_episode: int | None = 1300,
    title: str | None = None,
) -> dict[str, Any]:
    raw_contract = _extract_contract(content)
    if not isinstance(raw_contract, dict):
        return content

    repaired = deepcopy(raw_contract)
    scenes = repaired.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return content

    for scene_index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        beats = _ensure_scene(scene)
        if not beats:
            return content
        repair_scene_conflict(scene)
        harden_opening_hook(
            beats[0] if scene_index == 0 else None,
            scene if scene_index == 0 else None,
        )
        harden_final_cliffhanger(
            beats[-1] if scene_index == len(scenes) - 1 else None,
            scene,
        )
        repair_beats(scene, beats)
        align_scene_durations(scene, beats, scene_index == 0)
        dedupe_progression(beats)
        shorten_dialogue_lines(beats)
    ensure_contract_payoff(scenes)

    try:
        contract = normalize_script_beat_contract(repaired)
        flattened = flatten_contract_to_script_payload(
            contract,
            format_type=format_type,
            language=language,
            episode_number=episode_number,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=title,
        )
    except Exception:
        return content

    metadata = {**dict(content.get("metadata") or {}), **flattened["metadata"]}
    candidate = {
        **content,
        **flattened,
        "metadata": metadata,
        "structured_script_contract": contract.model_dump(mode="json"),
    }
    preserved, _details = repair_preserves_script_structure(
        before=content,
        repaired=candidate,
    )
    return candidate if preserved else content


def _extract_contract(content: dict[str, Any]) -> dict[str, Any] | None:
    metadata = (
        content.get("metadata") if isinstance(content.get("metadata"), dict) else {}
    )
    top_level = (
        {
            key: value
            for key, value in content.items()
            if key not in {"metadata", "structured_script_contract"}
        }
        if isinstance(content.get("scenes"), list)
        else None
    )
    candidates = [
        content.get("structured_script_contract"),
        top_level,
        metadata.get("structured_script_contract"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and _can_normalize(candidate):
            return candidate
    return None


def _ensure_scene(scene: dict[str, Any]) -> list[dict[str, Any]]:
    beats = scene.get("beats")
    if not isinstance(beats, list) or len(beats) < 3:
        return []
    for order, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            return []
        beat["order_index"] = order
    return [beat for beat in beats if isinstance(beat, dict)]


def _can_normalize(payload: dict[str, Any]) -> bool:
    try:
        normalize_script_beat_contract(payload)
        return True
    except Exception:
        return False
