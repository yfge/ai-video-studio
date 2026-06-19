from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import (
    SCRIPT_BEAT_CONTRACT_VERSION,
    BeatType,
    SceneRole,
    StructuredScriptContract,
)
from app.services.ai.script_text import build_script_text
from app.services.script.beat_contract_canonicalizer import canonicalize_contract_enums
from app.services.script.beat_contract_flatten import contract_to_legacy_lines
from app.services.script.scene_utils import to_int

_SCENE_ROLES = set(SceneRole.__args__)
_BEAT_TYPES = set(BeatType.__args__)


def normalize_script_beat_contract(payload: dict[str, Any]) -> StructuredScriptContract:
    raw_contract = _extract_embedded_contract(payload)
    if raw_contract is not None:
        return StructuredScriptContract.model_validate(
            canonicalize_contract_enums(raw_contract)
        )
    if _looks_like_contract(payload):
        return StructuredScriptContract.model_validate(
            canonicalize_contract_enums(payload)
        )
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
    scenes, dialogues, stage_directions = contract_to_legacy_lines(contract)

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
                "dramatic_role": _literal_or_default(
                    scene.get("dramatic_role"), _SCENE_ROLES, "transition"
                ),
                "conflict": {
                    "question": scene.get("conflict_question") or str(summary),
                    "stakes": scene.get("stakes") or "本场必须推进剧情信息。",
                    "opposition": scene.get("opposition") or "阻碍尚未结构化。",
                    "turn": scene.get("turn"),
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": _literal_or_default(
                            scene.get("beat_type"), _BEAT_TYPES, "setup"
                        ),
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


def _items_for_scene(items: list[Any], scene_no: int) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if isinstance(item, dict) and to_int(item.get("scene_number")) == scene_no
    ]


def _has_fallback(items: list[Any]) -> bool:
    return any(isinstance(item, dict) and item.get("fallback") for item in items)


def _literal_or_default(value: Any, allowed: set[str], default: str) -> str:
    raw = str(value or "").strip()
    return raw if raw in allowed else default


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
