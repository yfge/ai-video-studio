from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.duration_orchestrator.state import SceneBudget
from app.utils.json_utils import extract_json_block

BuildWordCountConstraints = Callable[[List[SceneBudget], List[Dict[str, Any]]], str]


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _filter_scene_items(
    items: Sequence[Dict[str, Any]],
    allowed_scene_numbers: Set[int],
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        scene_no = _to_int(item.get("scene_number"))
        if scene_no in allowed_scene_numbers:
            filtered.append(item)
    return filtered


def _exclude_scene_items(
    items: Sequence[Dict[str, Any]],
    excluded_scene_numbers: Set[int],
) -> List[Dict[str, Any]]:
    kept: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        scene_no = _to_int(item.get("scene_number"))
        if scene_no not in excluded_scene_numbers:
            kept.append(item)
    return kept


async def try_fill_pending_scenes_after_react(
    *,
    ai_manager: Any,
    episode: Dict[str, Any],
    story: Dict[str, Any],
    scenes: Sequence[Dict[str, Any]],
    pending_budgets: Sequence[SceneBudget],
    dialogue_style: str,
    language: str,
    format_type: str,
    temperature: float,
    model: Optional[str],
    prefer_provider: Optional[str],
    existing_dialogues: Sequence[Dict[str, Any]],
    existing_stage_directions: Sequence[Dict[str, Any]],
    build_word_count_constraints: BuildWordCountConstraints,
) -> Optional[Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[int]]]:
    """Try to fill missing/out-of-tolerance scenes after REACT max retries.

    This is a last-resort strategy to avoid accepting obviously incomplete
    results (e.g., early scenes missing dialogues) after repeated retries.
    """
    pending_scene_numbers = sorted(
        {b.scene_number for b in pending_budgets if b.scene_number}
    )
    if not pending_scene_numbers:
        return None
    pending_set = set(pending_scene_numbers)

    pending_scenes: List[Dict[str, Any]] = []
    for idx, sc in enumerate(scenes, start=1):
        if not isinstance(sc, dict):
            continue
        scene_no = _to_int(sc.get("scene_number")) or idx
        if scene_no in pending_set:
            pending_scenes.append(sc)

    if not pending_scenes:
        return None

    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_DIALOGUES.value,
        {
            "episode": episode,
            "story": story,
            "scenes": pending_scenes,
            "dialogue_style": dialogue_style,
            "language": language,
            "format_type": format_type,
        },
    )
    prompt = (
        prompt
        + "\n\n## 重要：仅补全以下场景\n"
        + f"你只能生成这些 scene_number 的对白与舞台指示：{pending_scene_numbers}\n"
        + "要求：每个场景至少 2-3 句对白，scene_number 必须为整数且准确。\n"
        + "不要输出其它场景的内容。\n"
    )

    constraints_text = build_word_count_constraints(
        list(pending_budgets), pending_scenes
    )
    prompt = prompt + constraints_text

    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.6, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={
            "name": "script_dialogues_fill_missing",
            "schema": {
                "type": "object",
                "properties": {
                    "dialogues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scene_number": {
                                    "anyOf": [{"type": "integer"}, {"type": "null"}]
                                },
                                "character": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}]
                                },
                                "content": {"type": "string"},
                                "emotion": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}]
                                },
                                "action": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}]
                                },
                            },
                        },
                    },
                    "stage_directions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scene_number": {
                                    "anyOf": [{"type": "integer"}, {"type": "null"}]
                                },
                                "timing": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}]
                                },
                                "content": {"type": "string"},
                                "type": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}]
                                },
                            },
                        },
                    },
                },
            },
        },
        system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
    )
    if not getattr(resp, "success", False):
        return None

    raw = resp.data if isinstance(resp.data, str) else str(resp.data)
    parsed = extract_json_block(raw)
    if not isinstance(parsed, dict):
        return None

    new_dialogues = _filter_scene_items(parsed.get("dialogues") or [], pending_set)
    new_stage = _filter_scene_items(parsed.get("stage_directions") or [], pending_set)
    if not new_dialogues and not new_stage:
        return None

    merged_dialogues = (
        _exclude_scene_items(existing_dialogues, pending_set) + new_dialogues
    )
    merged_stage = (
        _exclude_scene_items(existing_stage_directions, pending_set) + new_stage
    )

    return merged_dialogues, merged_stage, pending_scene_numbers
