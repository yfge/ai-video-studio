from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from app.services.script.beat_contract_flatten import contract_to_legacy_lines


def sync_structured_contract(
    payload: Dict[str, Any],
    *,
    scenes: list[Any] | None,
    dialogues: list[Any] | None,
    stage_directions: list[Any] | None,
) -> bool | None:
    raw_contract = payload.get("structured_script_contract")
    if not isinstance(raw_contract, dict):
        metadata = payload.get("metadata")
        raw_contract = (
            metadata.get("structured_script_contract")
            if isinstance(metadata, dict)
            else None
        )
    if not isinstance(raw_contract, dict):
        return None

    contract = deepcopy(raw_contract)
    contract_scenes = contract.get("scenes")
    if not isinstance(contract_scenes, list):
        return False
    scene_map = {
        scene_number: scene
        for scene in contract_scenes
        if isinstance(scene, dict)
        and (scene_number := _positive_int(scene.get("scene_number"))) is not None
    }
    _merge_scene_updates(scene_map, scenes)
    dialogue_groups = _group_lines_by_beat(dialogues)
    stage_groups = _group_lines_by_beat(stage_directions)

    for scene_number, scene in scene_map.items():
        beats = scene.get("beats")
        if not isinstance(beats, list):
            continue
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            beat_index = _positive_int(beat.get("order_index"))
            if beat_index is None:
                continue
            key = (scene_number, beat_index)
            if key in dialogue_groups:
                revised_dialogues = [
                    line
                    for item in dialogue_groups[key]
                    if (line := _dialogue_contract_line(item)) is not None
                ]
                if revised_dialogues:
                    beat["dialogue_lines"] = revised_dialogues
            if key in stage_groups:
                visible_event, action_lines = _stage_contract_lines(stage_groups[key])
                if visible_event:
                    beat["visible_event"] = visible_event
                if action_lines:
                    beat["action_lines"] = action_lines

    try:
        from app.services.script.beat_contract_normalizer import (
            normalize_script_beat_contract,
        )

        normalized = normalize_script_beat_contract(
            {"structured_script_contract": contract}
        )
        synced_contract = normalized.model_dump(mode="json")
        flat_scenes, flat_dialogues, flat_stage = contract_to_legacy_lines(normalized)
    except Exception:
        return False

    payload["structured_script_contract"] = synced_contract
    metadata = payload.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["structured_script_contract"] = synced_contract
    payload["scenes"] = flat_scenes
    payload["dialogues"] = flat_dialogues
    payload["stage_directions"] = flat_stage
    return True


def _merge_scene_updates(
    scene_map: dict[int, Dict[str, Any]],
    scenes: list[Any] | None,
) -> None:
    for source in scenes or []:
        if not isinstance(source, dict):
            continue
        scene_number = _positive_int(source.get("scene_number"))
        target = scene_map.get(scene_number or -1)
        if not target:
            continue
        for key in (
            "slug_line",
            "location",
            "time_of_day",
            "estimated_duration_seconds",
            "dramatic_role",
        ):
            if source.get(key) not in (None, ""):
                target[key] = source[key]
        source_conflict = source.get("conflict")
        if not isinstance(source_conflict, dict):
            source_conflict = source.get("conflict_notes")
        target_conflict = target.get("conflict")
        if isinstance(source_conflict, dict) and isinstance(target_conflict, dict):
            for key in ("question", "stakes", "opposition", "turn"):
                if source_conflict.get(key) not in (None, ""):
                    target_conflict[key] = source_conflict[key]


def _group_lines_by_beat(
    lines: list[Any] | None,
) -> dict[tuple[int, int], list[Dict[str, Any]]]:
    grouped: dict[tuple[int, int], list[Dict[str, Any]]] = {}
    for item in lines or []:
        if not isinstance(item, dict):
            continue
        scene_number = _positive_int(item.get("scene_number"))
        beat_index = _positive_int(item.get("beat_order_index"))
        if scene_number is None or beat_index is None:
            continue
        grouped.setdefault((scene_number, beat_index), []).append(item)
    return grouped


def _dialogue_contract_line(item: Dict[str, Any]) -> Dict[str, Any] | None:
    character = item.get("character") or item.get("speaker")
    content = item.get("content") or item.get("line") or item.get("text")
    if not character or not content:
        return None
    return {
        "character": str(character),
        "content": str(content),
        "emotion": item.get("emotion"),
        "action": item.get("action"),
    }


def _stage_contract_lines(
    items: list[Dict[str, Any]],
) -> tuple[str | None, list[Dict[str, Any]]]:
    visible_event: str | None = None
    actions: list[Dict[str, Any]] = []
    for item in items:
        content = item.get("content") or item.get("description")
        if not content:
            continue
        if item.get("type") == "visible_event" or item.get("timing") == "visible":
            visible_event = str(content)
            continue
        actions.append(
            {
                "content": str(content),
                "timing": item.get("timing"),
                "type": item.get("type"),
            }
        )
    return visible_event, actions


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
