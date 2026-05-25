"""Shared text-generation payloads for the mock AI service fixture."""

from __future__ import annotations

from typing import Any


def mock_generate_text_payload(prompt: str, json_schema: Any) -> dict[str, Any]:
    schema_name = json_schema.get("name") if isinstance(json_schema, dict) else ""
    if schema_name == "script_cliffhanger_judgement":
        return {
            "passed": True,
            "score": 0.95,
            "reason": "mock script ends on an unresolved question",
            "evidence": "Which door does the key open?",
            "suggestion": "",
        }
    if "The generated script JSON failed strict quality gate validation" in prompt:
        return _script_repair_payload()
    if "投流表" in prompt or "Traffic Sheet" in prompt:
        return _traffic_sheet_payload()
    return _script_score_payload()


def _script_repair_payload() -> dict[str, Any]:
    return {
        "content": (
            "【音效】砰！画面直接切入冲突现场。\n"
            "# screenplay (zh-CN)\n"
            "## 场景\n"
            "- [场景 1] Scene 1: 旁白 finds the hidden key.\n"
            "【快】【情绪目的：推进冲突】旁白 grabs the key before the door opens.\n"
            "\n## 对白\n"
            "[场景 1] 旁白: Stop now?\n"
            "\n## 舞台指示\n"
            "[场景 1][mid] 旁白 hides the key under the lamp.\n"
            "【慢】【情绪目的：留下悬念】Which door does the key open?"
        ),
        "scenes": [
            {
                "scene_number": 1,
                "location": "Room",
                "time": "Day",
                "description": "Mock scene description",
            }
        ],
        "dialogues": [{"scene_number": 1, "character": "旁白", "content": "Stop now?"}],
        "stage_directions": [
            {"scene_number": 1, "content": "Camera pans across the room."}
        ],
    }


def _traffic_sheet_payload() -> dict[str, Any]:
    return {
        "episode_id": 1,
        "script_id": 1,
        "market_region": "NA",
        "micro_genre": "test",
        "assets": [
            {
                "asset_id": "ep1_asset01_15s",
                "duration_seconds": 15,
                "market_region": "NA",
                "micro_genre": "test",
                "hook_type": "reveal",
                "source_episode": 1,
                "source_timecode_start": "00:00:00",
                "source_timecode_end": "00:00:15",
                "key_line": "mock line",
                "visual_hook": "mock visual",
                "shot_list": ["shot 1"],
                "cliff_or_cta": "mock cta",
                "music_reference": None,
                "compliance_flags": [],
            }
        ],
    }


def _script_score_payload() -> dict[str, Any]:
    return {
        "overall_score": 4.2,
        "dimension_scores": {
            "conflict_intensity": 4.5,
            "character_recognizability": 4.0,
            "cultural_fit": 4.5,
            "clip_ability": 4.0,
            "logic_coherence": 4.0,
        },
        "verdict": "pass",
        "strengths": ["mock strength"],
        "risks": [],
        "rewrite_guidance": [],
        "suggested_ad_hooks": ["mock hook"],
    }
