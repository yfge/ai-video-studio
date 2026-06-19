from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.services.quality_gate_core import (
    MAX_QUALITY_GATE_REPAIRS,
    NarrativeQualityGateError,
    build_quality_gate_report,
    make_quality_check,
)
from app.services.script_quality_gate_beat_contract import (
    beat_contract_check,
    required_beat_contract_check,
)
from app.services.script_quality_gate_checks import (
    dict_character_check,
    duration_check,
    fallback_dialogue_check,
    lint_check,
    result_flag_checks,
    schema_check,
    script_quality_check,
    story_model_character_check,
)

logger = logging.getLogger(__name__)


async def evaluate_script_quality_gate(
    *,
    content: Dict[str, Any],
    story: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    story_model: Any = None,
    episode_id: Optional[int] = None,
    db: Any = None,
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
    lint_threshold: float = 9.0,
    target_chars_per_episode: Optional[int] = None,
    ai_manager: Any = None,
    model: Optional[str] = None,
    prefer_provider: Optional[str] = None,
    require_beat_contract: bool = False,
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
    checks.append(fallback_dialogue_check(dialogues))
    checks.append(
        story_model_character_check(story_model, episode_id, db, scenes, dialogues)
        if story_model is not None
        else dict_character_check(story, dialogues)
    )
    checks.extend(result_flag_checks(result))

    quality_check = script_quality_check(content, story, result)
    if quality_check:
        checks.append(quality_check)

    if require_beat_contract:
        checks.append(required_beat_contract_check(content))

    beat_check = beat_contract_check(content)
    if beat_check:
        checks.append(beat_check)

    checks.append(duration_check(result))
    checks.append(
        await lint_check(
            content,
            lint_threshold,
            target_chars_per_episode,
            ai_manager=ai_manager,
            model=model,
            prefer_provider=prefer_provider,
        )
    )
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
    lint_threshold: float = 9.0,
    target_chars_per_episode: Optional[int] = None,
    require_beat_contract: bool = False,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    from app.services.script_quality_gate_repair_flow import (
        enforce_script_quality_gate_with_repair as enforce_repair_flow,
    )

    return await enforce_repair_flow(
        ai_manager=ai_manager,
        result=result,
        content=content,
        story=story,
        story_model=story_model,
        episode_id=episode_id,
        db=db,
        model=model,
        prefer_provider=prefer_provider,
        temperature=temperature,
        max_repairs=max_repairs,
        lint_threshold=lint_threshold,
        target_chars_per_episode=target_chars_per_episode,
        require_beat_contract=require_beat_contract,
    )
