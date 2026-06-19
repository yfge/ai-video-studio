from __future__ import annotations

from typing import Any, Dict


def script_score_json_schema() -> Dict[str, Any]:
    """Return provider-compatible schema without $defs/allOf wrappers."""

    score_field = {"type": "number", "minimum": 0, "maximum": 5}
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "overall_score": score_field,
            "dimension_scores": {
                "type": "object",
                "properties": {
                    "conflict_intensity": score_field,
                    "character_recognizability": score_field,
                    "cultural_fit": score_field,
                    "clip_ability": score_field,
                    "logic_coherence": score_field,
                },
                "required": [
                    "conflict_intensity",
                    "character_recognizability",
                    "cultural_fit",
                    "clip_ability",
                    "logic_coherence",
                ],
                "additionalProperties": False,
            },
            "verdict": {"type": "string", "enum": ["pass", "review", "rewrite"]},
            "strengths": string_array,
            "risks": string_array,
            "rewrite_guidance": string_array,
            "suggested_ad_hooks": string_array,
        },
        "required": [
            "overall_score",
            "dimension_scores",
            "verdict",
            "strengths",
            "risks",
            "rewrite_guidance",
            "suggested_ad_hooks",
        ],
        "additionalProperties": False,
    }
