from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from app.core.validators.script_dialogue_quality import looks_like_writer_note
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.duration_orchestrator.constants import WORDS_PER_SECOND
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

    base_prompt = prompt_manager.render_prompt(
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
    base_prompt = (
        base_prompt
        + "\n\n## 重要：仅补全以下场景\n"
        + f"你只能生成这些 scene_number 的对白与舞台指示：{pending_scene_numbers}\n"
        + "硬性要求：每个场景至少 2 句对白，scene_number 必须为整数且准确。\n"
        + "严禁输出编剧/助手元语言（如“这里可以…”），严禁跨场景重复模板台词。\n"
        + "不要输出其它场景的内容。\n"
    )

    constraints_text = build_word_count_constraints(
        list(pending_budgets), pending_scenes
    )
    base_prompt = base_prompt + constraints_text

    schema = {
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
                            "action": {"anyOf": [{"type": "string"}, {"type": "null"}]},
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
                            "timing": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "content": {"type": "string"},
                            "type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        },
                    },
                },
            },
        },
    }

    new_dialogues: List[Dict[str, Any]] = []
    new_stage: List[Dict[str, Any]] = []
    passed_constraints = False

    prompt = base_prompt
    budgets_by_scene = {b.scene_number: b for b in pending_budgets if b.scene_number}

    for attempt in range(3):
        resp = await ai_manager.generate_text(
            prompt=prompt,
            temperature=(
                min(0.6, temperature)
                if attempt == 0
                else (0.4 if attempt == 1 else 0.2)
            ),
            model=model,
            prefer_provider=prefer_provider,
            json_schema=schema,
            system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
        )
        if not getattr(resp, "success", False):
            continue

        parsed = (
            resp.data
            if isinstance(resp.data, dict)
            else extract_json_block(
                resp.data if isinstance(resp.data, str) else str(resp.data)
            )
        )
        if not isinstance(parsed, dict):
            continue

        new_dialogues = _filter_scene_items(parsed.get("dialogues") or [], pending_set)
        new_stage = _filter_scene_items(
            parsed.get("stage_directions") or [], pending_set
        )

        per_scene_counts = {
            s: len([d for d in new_dialogues if _to_int(d.get("scene_number")) == s])
            for s in pending_scene_numbers
        }
        has_writer_notes = any(
            looks_like_writer_note(str(d.get("content") or ""))
            for d in new_dialogues
            if isinstance(d, dict)
        )
        if has_writer_notes:
            prompt = (
                base_prompt
                + "\n\n## REACT 驳回\n"
                + "你输出了编剧/助手元语言（如“这里可以…”）。请全部改写为戏内台词，不要保留元语言。\n"
            )
            continue

        missing = [s for s, c in per_scene_counts.items() if c < 2]
        if not missing:
            # Additional guard: ensure dialogue duration is within scene budget tolerance.
            too_short: list[str] = []
            too_long: list[str] = []
            for scene_no in pending_scene_numbers:
                budget = budgets_by_scene.get(scene_no)
                if not budget:
                    continue
                total_chars = sum(
                    len(str(d.get("content") or ""))
                    for d in new_dialogues
                    if isinstance(d, dict)
                    and _to_int(d.get("scene_number")) == scene_no
                )
                est_seconds = total_chars / WORDS_PER_SECOND if total_chars > 0 else 0.0
                if budget.min_duration_seconds and est_seconds < float(
                    budget.min_duration_seconds
                ):
                    need = int(
                        (budget.target_duration_seconds - est_seconds)
                        * WORDS_PER_SECOND
                    )
                    min_chars = int(
                        float(budget.min_duration_seconds) * WORDS_PER_SECOND
                    )
                    too_short.append(
                        f"{scene_no}(当前≈{est_seconds:.1f}s，至少≈{budget.min_duration_seconds}s；字符数≥{min_chars}，建议再+{max(need, 20)}字)"
                    )
                elif budget.max_duration_seconds and est_seconds > float(
                    budget.max_duration_seconds
                ):
                    over = int(
                        (est_seconds - budget.target_duration_seconds)
                        * WORDS_PER_SECOND
                    )
                    too_long.append(
                        f"{scene_no}(当前≈{est_seconds:.1f}s，最多≈{budget.max_duration_seconds}s；建议删减≈{max(over, 20)}字)"
                    )

            if not too_short and not too_long:
                passed_constraints = True
                break

            reject_lines: list[str] = []
            if too_short:
                reject_lines.append("以下场景对白时长仍不足：" + "；".join(too_short))
            if too_long:
                reject_lines.append("以下场景对白时长过长：" + "；".join(too_long))

            prompt = (
                base_prompt
                + "\n\n## REACT 驳回（时长不达标）\n"
                + "\n".join(reject_lines)
                + "\n硬性要求：严格满足各场景字数/时长约束；只能输出指定 scene_number；禁止编剧/助手元语言与跨场景重复模板台词。\n"
            )
            continue

        prompt = (
            base_prompt
            + "\n\n## REACT 驳回\n"
            + f"以下场景对白条数仍不足 2 句：{missing}；当前计数：{per_scene_counts}\n"
            + "请仅针对这些场景补足到 2-3 句对白。\n"
        )

    if not passed_constraints:
        return None

    if not new_dialogues and not new_stage:
        return None

    merged_dialogues = (
        _exclude_scene_items(existing_dialogues, pending_set) + new_dialogues
    )
    merged_stage = (
        _exclude_scene_items(existing_stage_directions, pending_set) + new_stage
    )

    return merged_dialogues, merged_stage, pending_scene_numbers
