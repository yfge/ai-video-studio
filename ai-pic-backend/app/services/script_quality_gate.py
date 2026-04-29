from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from app.schemas.generation import ScriptModel
from app.services.quality_gate_core import (
    MAX_QUALITY_GATE_REPAIRS,
    NarrativeQualityGateError,
    build_quality_gate_report,
    make_quality_check,
    quality_gate_attempt_snapshot,
)
from app.services.quality_gate_repair import repair_quality_gate_payload
from app.services.script_quality_gate_checks import (
    dict_character_check,
    duration_check,
    lint_check,
    result_flag_checks,
    schema_check,
    script_quality_check,
    story_model_character_check,
)


def evaluate_script_quality_gate(
    *,
    content: Dict[str, Any],
    story: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    story_model: Any = None,
    episode_id: Optional[int] = None,
    db: Any = None,
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
    lint_threshold: float = 9.0,
) -> Dict[str, Any]:
    result = result or {}
    checks = [schema_check(content)]
    scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
    dialogues = (
        content.get("dialogues") if isinstance(content.get("dialogues"), list) else []
    )
    stage = (
        content.get("stage_directions")
        if isinstance(content.get("stage_directions"), list)
        else []
    )
    checks.extend(
        [
            make_quality_check(
                "script_scenes", bool(scenes), "script must contain scenes"
            ),
            make_quality_check(
                "script_dialogues", bool(dialogues), "script must contain dialogues"
            ),
            make_quality_check(
                "script_stage_directions",
                bool(stage),
                "script must contain stage directions",
            ),
        ]
    )
    checks.append(
        story_model_character_check(story_model, episode_id, db, scenes, dialogues)
        if story_model is not None
        else dict_character_check(story, dialogues)
    )
    checks.extend(result_flag_checks(result))

    quality_check = script_quality_check(content, story, result)
    if quality_check:
        checks.append(quality_check)

    checks.append(duration_check(result))
    checks.append(lint_check(content, lint_threshold))
    return build_quality_gate_report(
        kind="script", checks=checks, repair_attempts=repair_attempts
    )


async def enforce_script_quality_gate_with_repair(
    *,
    ai_manager: Any,
    result: Dict[str, Any],
    content: Dict[str, Any],
    story: Dict[str, Any],
    story_model: Any = None,
    episode_id: Optional[int] = None,
    db: Any = None,
    model: Optional[str] = None,
    prefer_provider: Optional[str] = None,
    temperature: float = 0.3,
    max_repairs: int = MAX_QUALITY_GATE_REPAIRS,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    attempts: list[Dict[str, Any]] = []
    content = deepcopy(content)
    gate = evaluate_script_quality_gate(
        content=content,
        story=story,
        result=result,
        story_model=story_model,
        episode_id=episode_id,
        db=db,
    )
    if gate["passed"]:
        return _with_script_gate(result, content, gate), content, gate

    for attempt in range(1, max_repairs + 1):
        repaired = await repair_quality_gate_payload(
            ai_manager=ai_manager,
            kind="script",
            payload=content,
            quality_gate=gate,
            schema={"name": "script", "schema": ScriptModel.model_json_schema()},
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        attempts.append(
            {
                "attempt": attempt,
                "input_gate": quality_gate_attempt_snapshot(gate),
                "repaired": bool(repaired),
            }
        )
        if not repaired:
            continue
        content = repaired
        gate = evaluate_script_quality_gate(
            content=content,
            story=story,
            result=result,
            story_model=story_model,
            episode_id=episode_id,
            db=db,
            repair_attempts=deepcopy(attempts),
        )
        attempts[-1]["output_gate"] = quality_gate_attempt_snapshot(gate)
        if gate["passed"]:
            return _with_script_gate(result, content, gate), content, gate

    gate["repair_attempts"] = attempts
    raise NarrativeQualityGateError("script", gate)


def _with_script_gate(
    result: Dict[str, Any], content: Dict[str, Any], gate: Dict[str, Any]
) -> Dict[str, Any]:
    updated = dict(result)
    updated["content"] = content
    updated["normalized"] = content
    updated["quality_gate"] = gate
    return updated
