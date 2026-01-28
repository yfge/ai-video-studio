from __future__ import annotations

from typing import Any, Dict

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


def build_agent_run(result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    return {
        "generation_method": result.get("generation_method"),
        "template_used": result.get("template_used"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "reasoning": result.get("reasoning"),
    }
