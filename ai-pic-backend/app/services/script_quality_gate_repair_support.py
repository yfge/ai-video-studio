from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.script_quality_gate_checks import story_model_character_check

SCRIPT_BEAT_CONTRACT_REPAIR_INSTRUCTIONS = """
Critical script repair instructions:
- Return the repaired script payload itself, not the quality_gate report and not a wrapper object.
- Preserve the top-level ScriptModel fields: content, scenes, dialogues, stage_directions, metadata, structured_script_contract.
- Keep structured_script_contract.contract_version as "script-beat-v1".
- Every structured_script_contract.scenes item must contain 3-5 beats with contiguous order_index values.
- Beat duration_seconds values in each scene must sum close to estimated_duration_seconds.
- Scene conflict.stakes must name a concrete external loss, asset, contract, deadline, money amount, file, permission, data, or client consequence.
- Scene conflict.opposition must name the concrete blocking source, such as a specific client, colleague, file, phone, recording, screen, deletion action, contract, or anonymous message.
- The first scene first beat must be beat_type "hook", duration_seconds <= 3, and show a visible immediate threat or reversal.
- The final scene final beat must be beat_type "cliffhanger" or include cliffhanger_tag with a specific unresolved threat.
- Do not remove existing scenes, dialogues, or stage_directions; add concrete beats and align metadata instead.
""".strip()


def refresh_unknown_speaker_validation_result(
    *,
    result: Dict[str, Any],
    content: Dict[str, Any],
    story_model: Any = None,
    episode_id: Optional[int] = None,
    db: Any = None,
) -> Dict[str, Any]:
    if result.get("character_validation_passed") is not False:
        return result
    if story_model is None or not _is_unknown_speaker_only_character_result(result):
        return result
    scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
    dialogues = content.get("dialogues") if isinstance(content.get("dialogues"), list) else []
    policy_check = story_model_character_check(
        story_model,
        episode_id,
        db,
        scenes,
        dialogues,
    )
    if not policy_check.get("passed"):
        return result
    updated = dict(result)
    updated["character_validation_passed"] = True
    updated["character_validation_results"] = [
        {
            "passed": True,
            "severity": "info",
            "message": "Unknown speakers resolved by story/episode character policy",
            "details": policy_check.get("details") or {},
        }
    ]
    updated["character_warnings"] = [
        warning
        for warning in updated.get("character_warnings") or []
        if "Unknown speaker" not in str(warning)
    ]
    updated["unknown_names"] = []
    return updated


def _is_unknown_speaker_only_character_result(result: Dict[str, Any]) -> bool:
    validations = result.get("character_validation_results")
    if not isinstance(validations, list) or not validations:
        return False
    for item in validations:
        if not isinstance(item, dict):
            return False
        message = str(item.get("message") or "").lower()
        details = item.get("details") if isinstance(item.get("details"), dict) else {}
        if "unknown speaker" not in message and not details.get("unknown_speakers"):
            return False
    return True
