"""Script generation request payload for provider-chain harnesses."""

from __future__ import annotations

from typing import Any

from scripts.harness.provider_chain_payloads import TEXT_MODEL, build_script_prompt

SCRIPT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["title", "logline", "characters", "scenes"],
    "properties": {
        "title": {"type": "string"},
        "logline": {"type": "string"},
        "characters": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "role",
                    "appearance_prompt",
                    "consistency_anchor",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "appearance_prompt": {"type": "string"},
                    "consistency_anchor": {"type": "string"},
                },
            },
        },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "scene_id",
                    "duration_seconds",
                    "question",
                    "stakes",
                    "opposition",
                    "turn",
                    "plot",
                    "dialogue",
                    "beats",
                    "image_prompt",
                    "video_prompt",
                ],
                "properties": {
                    "scene_id": {"type": "string"},
                    "duration_seconds": {"type": "integer"},
                    "question": {"type": "string"},
                    "stakes": {"type": "string"},
                    "opposition": {"type": "string"},
                    "turn": {"type": "string"},
                    "plot": {"type": "string"},
                    "dialogue": {"type": "array"},
                    "beats": {"type": "array"},
                    "image_prompt": {"type": "string"},
                    "video_prompt": {"type": "string"},
                },
            },
        },
    },
}


def build_script_generation_request(
    mode: str,
    premise: str | None,
    repair_notes: list[str] | None,
) -> dict[str, Any]:
    """Build the text-generation API body for provider-chain scripts."""
    return {
        "prompt": build_script_prompt(mode, premise, repair_notes),
        "model": TEXT_MODEL,
        "prefer_provider": "deepseek",
        "system_prompt": "You are a strict JSON writer. Output JSON only.",
        "temperature": 0.2,
        "max_tokens": 2600,
        "stream": False,
        "thinking": False,
        "json_schema": {"name": "provider_chain_script", "schema": SCRIPT_JSON_SCHEMA},
    }
