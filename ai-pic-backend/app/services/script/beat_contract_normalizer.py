from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import (
    SCRIPT_BEAT_CONTRACT_VERSION,
    BeatType,
    SceneRole,
    StructuredScriptContract,
)
from app.services.ai.script_text import build_script_text
from app.services.script.scene_utils import to_int

_SCENE_ROLES = set(SceneRole.__args__)
_BEAT_TYPES = set(BeatType.__args__)


def normalize_script_beat_contract(payload: dict[str, Any]) -> StructuredScriptContract:
    raw_contract = _extract_embedded_contract(payload)
    if raw_contract is not None:
        return StructuredScriptContract.model_validate(raw_contract)
    if _looks_like_contract(payload):
        return StructuredScriptContract.model_validate(payload)
    return _legacy_payload_to_contract(payload)


def flatten_contract_to_script_payload(
    contract: StructuredScriptContract,
    *,
    format_type: str,
    language: str,
    episode_number: int | None,
    template_style: str | None,
    target_chars_per_episode: int | None,
    title: str | None,
) -> dict[str, Any]:
    scenes = [_scene_to_legacy(scene) for scene in contract.scenes]
    dialogues: list[dict[str, Any]] = []
    stage_directions: list[dict[str, Any]] = []
    for scene in contract.scenes:
        for beat in scene.beats:
            for line in beat.dialogue_lines:
                dialogues.append(
                    {
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "character": line.character,
                        "content": line.content,
                        "emotion": line.emotion,
                        "action": line.action,
                    }
                )
            for action in beat.action_lines:
                stage_directions.append(
                    {
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "timing": action.timing,
                        "content": action.content,
                        "type": action.type or "action",
                    }
                )

    contract_payload = contract.model_dump(mode="json")
    content = build_script_text(
        scenes,
        dialogues,
        stage_directions,
        format_type=format_type,
        language=language,
        episode_number=episode_number,
        template_style=template_style,
        target_chars_per_episode=target_chars_per_episode,
        title=title or contract.title,
    )
    return {
        "content": content,
        "scenes": scenes,
        "dialogues": dialogues,
        "stage_directions": stage_directions,
        "metadata": {
            "structured_contract_version": SCRIPT_BEAT_CONTRACT_VERSION,
            "structured_script_contract": contract_payload,
            "title": contract.title,
            "logline": contract.logline,
            "total_scenes": len(scenes),
            "total_dialogues": len(dialogues),
        },
        "structured_script_contract": contract_payload,
    }


def _extract_embedded_contract(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw = payload.get("structured_script_contract")
    if not isinstance(raw, dict):
        metadata = payload.get("metadata")
        raw = (
            metadata.get("structured_script_contract")
            if isinstance(metadata, dict)
            else None
        )
    return raw if isinstance(raw, dict) else None


def _looks_like_contract(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
        return False
    if payload.get("contract_version") == SCRIPT_BEAT_CONTRACT_VERSION:
        return True
    return any(
        isinstance(scene, dict) and isinstance(scene.get("beats"), list)
        for scene in payload["scenes"]
    )


def _legacy_payload_to_contract(payload: dict[str, Any]) -> StructuredScriptContract:
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    dialogues = (
        payload.get("dialogues") if isinstance(payload.get("dialogues"), list) else []
    )
    stage = (
        payload.get("stage_directions")
        if isinstance(payload.get("stage_directions"), list)
        else []
    )
    fallback_detected = _has_fallback(dialogues) or _has_fallback(stage)
    converted: dict[str, Any] = {
        "contract_version": SCRIPT_BEAT_CONTRACT_VERSION,
        "title": payload.get("title"),
        "logline": payload.get("logline"),
        "scenes": [],
    }
    for idx, raw_scene in enumerate(scenes, start=1):
        scene = (
            dict(raw_scene)
            if isinstance(raw_scene, dict)
            else {"summary": str(raw_scene)}
        )
        scene_no = to_int(scene.get("scene_number")) or idx
        scene_dialogues = _items_for_scene(dialogues, scene_no)
        scene_stage = _items_for_scene(stage, scene_no)
        summary = _scene_summary(scene, scene_no)
        converted["scenes"].append(
            {
                "scene_number": scene_no,
                "slug_line": scene.get("slug_line") or str(summary)[:80],
                "location": scene.get("location") or scene.get("place"),
                "time_of_day": scene.get("time_of_day") or scene.get("time"),
                "estimated_duration_seconds": to_int(
                    scene.get("estimated_duration_seconds")
                    or scene.get("duration_seconds")
                ),
                "dramatic_role": _scene_role(scene.get("dramatic_role")),
                "conflict": {
                    "question": scene.get("conflict_question") or str(summary),
                    "stakes": scene.get("stakes") or "本场必须推进剧情信息。",
                    "opposition": scene.get("opposition") or "阻碍尚未结构化。",
                    "turn": scene.get("turn"),
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": _beat_type(scene.get("beat_type")),
                        "dramatic_purpose": scene.get("notes") or str(summary),
                        "visible_event": str(summary),
                        "action_lines": [
                            {
                                "content": _line_content(item, fallback=str(summary)),
                                "timing": item.get("timing"),
                                "type": item.get("type") or "action",
                            }
                            for item in scene_stage
                            if isinstance(item, dict)
                        ],
                        "dialogue_lines": [
                            {
                                "character": item.get("character")
                                or item.get("speaker")
                                or "旁白",
                                "content": _line_content(item, fallback=str(summary)),
                                "emotion": item.get("emotion"),
                                "action": item.get("action"),
                            }
                            for item in scene_dialogues
                            if isinstance(item, dict)
                        ],
                        "duration_seconds": scene.get("estimated_duration_seconds"),
                    }
                ],
            }
        )
    contract = StructuredScriptContract.model_validate(converted)
    if fallback_detected:
        contract.model_extra["fallback_detected"] = True
    return contract


def _scene_to_legacy(scene) -> dict[str, Any]:
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


def _items_for_scene(items: list[Any], scene_no: int) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if isinstance(item, dict) and to_int(item.get("scene_number")) == scene_no
    ]


def _has_fallback(items: list[Any]) -> bool:
    return any(isinstance(item, dict) and item.get("fallback") for item in items)


def _scene_role(value: Any) -> str:
    raw = str(value or "").strip()
    return raw if raw in _SCENE_ROLES else "transition"


def _beat_type(value: Any) -> str:
    raw = str(value or "").strip()
    return raw if raw in _BEAT_TYPES else "setup"


def _line_content(item: dict[str, Any], *, fallback: str) -> str:
    for key in ("content", "direction", "description", "line", "text"):
        if item.get(key):
            return str(item[key])
    return fallback


def _scene_summary(scene: dict[str, Any], scene_no: int) -> str:
    for key in ("summary", "description", "conflict_question", "slug_line"):
        if scene.get(key):
            return str(scene[key])
    return f"场景 {scene_no}"
