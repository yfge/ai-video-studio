from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

_EXTRA_METADATA_EXCLUDE = {
    "premise",
    "synopsis",
    "main_conflict",
    "resolution",
    "main_characters",
    "character_relationships",
}


def build_extra_metadata(ai_content: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(ai_content, dict):
        return {}
    return {k: v for k, v in ai_content.items() if k not in _EXTRA_METADATA_EXCLUDE}


def resolve_model_provider(
    model_id: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    prefer_provider = None
    resolved_model = model_id
    if model_id and ":" in model_id:
        prefer_provider, resolved_model = model_id.split(":", 1)
    return prefer_provider, resolved_model


def build_agent_run(result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    payload: Dict[str, Any] = {
        "generation_method": result.get("generation_method"),
        "template_used": result.get("template_used"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "reasoning": result.get("reasoning"),
        "generation_mode": result.get("generation_mode"),
        "production_mode": result.get("production_mode"),
        "prompt_version": result.get("prompt_version"),
        "contract_version": result.get("contract_version"),
    }
    for key in (
        "character_validation_passed",
        "character_validation_results",
        "character_warnings",
        "story_quality_passed",
        "story_quality_result",
        "story_quality_warnings",
    ):
        if key in result:
            payload[key] = result.get(key)

    # Persist structured output audit trail for tasks UI (Task.parameters.agent_run).
    raw_content = result.get("content")
    if isinstance(raw_content, str) and raw_content.strip():
        payload["raw_content"] = raw_content
    normalized = result.get("normalized")
    if isinstance(normalized, dict) and normalized:
        payload["normalized"] = normalized
    validation_errors = result.get("validation_errors")
    if validation_errors:
        payload["validation_errors"] = validation_errors
    repair_attempts = result.get("repair_attempts")
    if repair_attempts:
        payload["repair_attempts"] = repair_attempts
    first_attempt = result.get("first_attempt")
    if first_attempt:
        payload["first_attempt"] = first_attempt
    quality_gate = result.get("quality_gate")
    if quality_gate:
        payload["quality_gate"] = quality_gate

    return {k: v for k, v in payload.items() if v is not None}
