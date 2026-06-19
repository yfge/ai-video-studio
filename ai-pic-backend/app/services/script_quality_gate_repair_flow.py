from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Dict, Optional

from app.schemas.generation import ScriptModel
from app.services.quality_gate_core import (
    MAX_QUALITY_GATE_REPAIRS,
    NarrativeQualityGateError,
    quality_gate_attempt_snapshot,
)
from app.services.quality_gate_repair import repair_quality_gate_payload
from app.services.script.beat_contract_auto_repair import (
    auto_repair_script_beat_contract,
)
from app.services.script_quality_gate_auto_characters import (
    auto_create_temporary_characters_for_gate,
    with_auto_created_characters,
)
from app.services.script_quality_gate_repair_guard import (
    repair_preserves_script_structure,
)
from app.services.script_quality_gate_repair_support import (
    SCRIPT_BEAT_CONTRACT_REPAIR_INSTRUCTIONS,
    refresh_unknown_speaker_validation_result,
)

logger = logging.getLogger(__name__)

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
    from app.services.script_quality_gate import evaluate_script_quality_gate

    attempts: list[Dict[str, Any]] = []
    content = _auto_repair_beat_contract(
        deepcopy(content),
        require_beat_contract=require_beat_contract,
        target_chars_per_episode=target_chars_per_episode,
    )
    auto_created_characters: list[Dict[str, Any]] = []
    gate_options = {
        "story": story,
        "story_model": story_model,
        "episode_id": episode_id,
        "db": db,
        "lint_threshold": lint_threshold,
        "target_chars_per_episode": target_chars_per_episode,
        "ai_manager": ai_manager,
        "model": model,
        "prefer_provider": prefer_provider,
        "require_beat_contract": require_beat_contract,
    }
    gate = await evaluate_script_quality_gate(content=content, result=result, **gate_options)
    result, gate = await _refresh_gate(
        evaluate_script_quality_gate,
        result=result,
        gate=gate,
        content=content,
        gate_options=gate_options,
    )
    result, gate = await _apply_auto_characters(
        evaluate_script_quality_gate,
        result=result,
        gate=gate,
        content=content,
        auto_created_characters=auto_created_characters,
        gate_options=gate_options,
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
            model=model or ("deepseek-v4-flash" if require_beat_contract else result.get("model_used")),
            prefer_provider=prefer_provider or ("deepseek" if require_beat_contract else result.get("provider_used")),
            temperature=temperature,
            extra_instructions=SCRIPT_BEAT_CONTRACT_REPAIR_INSTRUCTIONS
            if require_beat_contract
            else None,
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
        structure_ok, structure_details = repair_preserves_script_structure(
            before=content,
            repaired=repaired,
        )
        attempts[-1]["structure_guard"] = structure_details
        if not structure_ok:
            logger.warning("Rejected script quality repair that lost structure")
            continue
        content = _auto_repair_beat_contract(
            repaired,
            require_beat_contract=require_beat_contract,
            target_chars_per_episode=target_chars_per_episode,
        )
        gate = await evaluate_script_quality_gate(
            content=content,
            result=result,
            repair_attempts=deepcopy(attempts),
            **gate_options,
        )
        result, gate = await _refresh_gate(
            evaluate_script_quality_gate,
            result=result,
            gate=gate,
            content=content,
            gate_options=gate_options,
            repair_attempts=deepcopy(attempts),
        )
        result, gate = await _apply_auto_characters(
            evaluate_script_quality_gate,
            result=result,
            gate=gate,
            content=content,
            auto_created_characters=auto_created_characters,
            gate_options=gate_options,
            repair_attempts=deepcopy(attempts),
        )
        attempts[-1]["output_gate"] = quality_gate_attempt_snapshot(gate)
        if gate["passed"]:
            return _with_script_gate(result, content, gate), content, gate

    gate["repair_attempts"] = attempts
    raise NarrativeQualityGateError("script", gate)


def _auto_repair_beat_contract(
    content: Dict[str, Any],
    *,
    require_beat_contract: bool,
    target_chars_per_episode: Optional[int],
) -> Dict[str, Any]:
    if not require_beat_contract:
        return content
    return auto_repair_script_beat_contract(
        content,
        target_chars_per_episode=target_chars_per_episode,
    )


async def _refresh_gate(
    evaluate_gate: Any,
    *,
    result: Dict[str, Any],
    gate: Dict[str, Any],
    content: Dict[str, Any],
    gate_options: Dict[str, Any],
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    refreshed = refresh_unknown_speaker_validation_result(
        result=result,
        content=content,
        story_model=gate_options.get("story_model"),
        episode_id=gate_options.get("episode_id"),
        db=gate_options.get("db"),
    )
    if refreshed == result:
        return result, gate
    return refreshed, await evaluate_gate(
        content=content,
        result=refreshed,
        repair_attempts=repair_attempts,
        **gate_options,
    )


async def _apply_auto_characters(
    evaluate_gate: Any,
    *,
    result: Dict[str, Any],
    gate: Dict[str, Any],
    content: Dict[str, Any],
    auto_created_characters: list[Dict[str, Any]],
    gate_options: Dict[str, Any],
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    created = await auto_create_temporary_characters_for_gate(
        gate=gate,
        content=content,
        story_model=gate_options.get("story_model"),
        episode_id=gate_options.get("episode_id"),
        db=gate_options.get("db"),
    )
    if not created:
        return result, gate
    auto_created_characters.extend(created)
    result = with_auto_created_characters(result, auto_created_characters)
    return await _refresh_gate(
        evaluate_gate,
        result=result,
        gate=gate,
        content=content,
        gate_options=gate_options,
        repair_attempts=repair_attempts,
    )


def _with_script_gate(
    result: Dict[str, Any], content: Dict[str, Any], gate: Dict[str, Any]
) -> Dict[str, Any]:
    return {**result, "content": content, "normalized": content, "quality_gate": gate}
