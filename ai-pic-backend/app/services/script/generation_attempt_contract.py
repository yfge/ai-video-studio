from __future__ import annotations

from typing import Any, Dict

from app.models.script import Episode
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)


def attempt_temperature(attempt_no: int, requested_temperature: Any) -> float:
    try:
        temperature = float(requested_temperature)
    except (TypeError, ValueError):
        temperature = 0.7
    if attempt_no <= 1:
        return temperature
    return min(temperature, 0.35)


def has_beat_contract_payload(content: Dict[str, Any]) -> bool:
    if isinstance(content.get("structured_script_contract"), dict):
        return True
    metadata = content.get("metadata")
    if isinstance(metadata, dict) and isinstance(
        metadata.get("structured_script_contract"), dict
    ):
        return True
    scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
    return any(
        isinstance(scene, dict) and isinstance(scene.get("beats"), list)
        for scene in scenes
    )


def apply_beat_contract_payload(
    ai_content: Dict[str, Any],
    *,
    script_content: str,
    scenes: list[Dict[str, Any]],
    dialogues: list[Dict[str, Any]],
    stage_directions: list[Dict[str, Any]],
    request_dict: Dict[str, Any],
    episode: Episode,
) -> tuple[
    Dict[str, Any],
    str,
    list[Dict[str, Any]],
    list[Dict[str, Any]],
    list[Dict[str, Any]],
]:
    try:
        flattened = _flatten_beat_contract_payload(
            ai_content,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            request_dict=request_dict,
            episode=episode,
        )
    except Exception as exc:
        metadata = dict(ai_content.get("metadata") or {})
        metadata["structured_script_contract_error"] = str(exc)
        return (
            {**ai_content, "metadata": metadata},
            script_content,
            scenes,
            dialogues,
            stage_directions,
        )

    metadata = {
        **dict(ai_content.get("metadata") or {}),
        **flattened.get("metadata", {}),
    }
    updated = {**ai_content, **flattened, "metadata": metadata}
    return (
        updated,
        flattened["content"],
        flattened["scenes"],
        flattened["dialogues"],
        flattened["stage_directions"],
    )


def _flatten_beat_contract_payload(
    ai_content: Dict[str, Any],
    *,
    scenes: list[Dict[str, Any]],
    dialogues: list[Dict[str, Any]],
    stage_directions: list[Dict[str, Any]],
    request_dict: Dict[str, Any],
    episode: Episode,
) -> Dict[str, Any]:
    beat_contract = normalize_script_beat_contract(
        {
            **ai_content,
            "scenes": scenes,
            "dialogues": dialogues,
            "stage_directions": stage_directions,
        }
    )
    return flatten_contract_to_script_payload(
        beat_contract,
        format_type=request_dict.get("format_type", "screenplay"),
        language=request_dict.get("language", "zh-CN"),
        episode_number=episode.episode_number,
        template_style=request_dict.get("template_style", "commercial_vertical_drama"),
        target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
        title=episode.title,
    )
