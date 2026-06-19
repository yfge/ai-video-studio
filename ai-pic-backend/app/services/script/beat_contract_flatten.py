from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import StructuredScriptContract


def contract_to_legacy_lines(
    contract: StructuredScriptContract,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scenes = [_scene_to_legacy(scene) for scene in contract.scenes]
    dialogues: list[dict[str, Any]] = []
    stage_directions: list[dict[str, Any]] = []
    for scene in contract.scenes:
        for beat in scene.beats:
            stage_directions.append(_visible_event_line(scene, beat))
            dialogues.extend(_dialogue_lines(scene, beat))
            stage_directions.extend(_action_lines(scene, beat))
    return scenes, dialogues, stage_directions


def _visible_event_line(scene: Any, beat: Any) -> dict[str, Any]:
    return {
        "scene_number": scene.scene_number,
        "beat_order_index": beat.order_index,
        "beat_type": beat.beat_type,
        "timing": "visible",
        "content": beat.visible_event,
        "type": "visible_event",
        "duration_seconds": beat.duration_seconds,
    }


def _dialogue_lines(scene: Any, beat: Any) -> list[dict[str, Any]]:
    return [
        {
            "scene_number": scene.scene_number,
            "beat_order_index": beat.order_index,
            "beat_type": beat.beat_type,
            "character": line.character,
            "content": line.content,
            "emotion": line.emotion,
            "action": line.action,
            "duration_seconds": beat.duration_seconds,
        }
        for line in beat.dialogue_lines
    ]


def _action_lines(scene: Any, beat: Any) -> list[dict[str, Any]]:
    return [
        {
            "scene_number": scene.scene_number,
            "beat_order_index": beat.order_index,
            "beat_type": beat.beat_type,
            "timing": action.timing,
            "content": action.content,
            "type": action.type or "action",
            "duration_seconds": beat.duration_seconds,
        }
        for action in beat.action_lines
    ]


def _scene_to_legacy(scene: Any) -> dict[str, Any]:
    return {
        "scene_number": scene.scene_number,
        "slug_line": scene.slug_line,
        "location": scene.location,
        "time_of_day": scene.time_of_day,
        "summary": scene.conflict.question,
        "description": scene.conflict.question,
        "estimated_duration_seconds": scene.estimated_duration_seconds,
        "dramatic_role": scene.dramatic_role,
        "conflict_notes": scene.conflict.model_dump(mode="json"),
        "beats": [beat.model_dump(mode="json") for beat in scene.beats],
    }
