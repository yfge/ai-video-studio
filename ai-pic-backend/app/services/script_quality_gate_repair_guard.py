from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict

_LOW_VALUE_CHARACTERS = {"旁白", "录音", "短信", "角色", "主角"}
_GENERIC_ANCHORS = {
    "http",
    "https",
    "json",
    "script",
    "scene",
    "screenplay",
}


def repair_preserves_script_structure(
    *,
    before: Dict[str, Any],
    repaired: Dict[str, Any],
) -> tuple[bool, Dict[str, Any]]:
    before_counts = _script_structure_counts(before)
    repaired_counts = _script_structure_counts(repaired)
    lost_fields = [
        field
        for field in ("scenes", "dialogues", "stage_directions")
        if before_counts[field] > 0 and repaired_counts[field] < before_counts[field]
    ]
    content_too_short = before_counts["content_chars"] >= 120 and repaired_counts[
        "content_chars"
    ] < max(80, int(before_counts["content_chars"] * 0.25))
    before_characters = _script_character_counts(before)
    repaired_characters = _script_character_counts(repaired)
    dominant_character = (
        before_characters.most_common(1)[0][0] if before_characters else None
    )
    dominant_character_lost = bool(
        dominant_character and repaired_characters[dominant_character] == 0
    )
    before_anchors = _script_anchor_terms(before)
    repaired_anchors = _script_anchor_terms(repaired)
    preserved_anchors = before_anchors & repaired_anchors
    required_anchor_count = (
        min(2, max(1, math.ceil(len(before_anchors) * 0.5))) if before_anchors else 0
    )
    anchor_terms_lost = len(preserved_anchors) < required_anchor_count
    before_contract = _beat_contract_coverage(before)
    repaired_contract = _beat_contract_coverage(repaired)
    contract_invalid = bool(before_contract["valid"] and not repaired_contract["valid"])
    contract_scenes_lost = bool(
        before_contract["valid"]
        and repaired_contract["valid"]
        and repaired_contract["scene_count"] < before_contract["scene_count"]
    )
    contract_beats_lost = bool(
        before_contract["valid"]
        and repaired_contract["valid"]
        and repaired_contract["beat_count"] < before_contract["beat_count"]
    )
    contract_action_coverage_lost = bool(
        before_contract["valid"]
        and before_contract["action_count"] > 0
        and repaired_contract["action_count"] == 0
    )
    contract_dialogue_coverage_lost = bool(
        before_contract["valid"]
        and before_contract["dialogue_count"] > 0
        and repaired_contract["dialogue_count"] == 0
    )
    passed = (
        not lost_fields
        and not content_too_short
        and not dominant_character_lost
        and not anchor_terms_lost
        and not contract_invalid
        and not contract_scenes_lost
        and not contract_beats_lost
        and not contract_action_coverage_lost
        and not contract_dialogue_coverage_lost
    )
    return (
        passed,
        {
            "passed": passed,
            "before": before_counts,
            "after": repaired_counts,
            "lost_fields": lost_fields,
            "content_too_short": content_too_short,
            "dominant_character": dominant_character,
            "dominant_character_lost": dominant_character_lost,
            "before_anchor_terms": sorted(before_anchors),
            "preserved_anchor_terms": sorted(preserved_anchors),
            "anchor_terms_lost": anchor_terms_lost,
            "before_contract": before_contract,
            "after_contract": repaired_contract,
            "contract_invalid": contract_invalid,
            "contract_scenes_lost": contract_scenes_lost,
            "contract_beats_lost": contract_beats_lost,
            "contract_action_coverage_lost": contract_action_coverage_lost,
            "contract_dialogue_coverage_lost": contract_dialogue_coverage_lost,
        },
    )


def _script_structure_counts(payload: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for field in ("scenes", "dialogues", "stage_directions"):
        value = payload.get(field)
        counts[field] = len(value) if isinstance(value, list) else 0
    counts["content_chars"] = len(str(payload.get("content") or ""))
    return counts


def _script_character_counts(payload: Dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in payload.get("dialogues") or []:
        _count_character(counts, line)
    contract = _structured_contract(payload)
    for scene in contract.get("scenes") or []:
        if not isinstance(scene, dict):
            continue
        for beat in scene.get("beats") or []:
            if not isinstance(beat, dict):
                continue
            for line in beat.get("dialogue_lines") or []:
                _count_character(counts, line)
    return counts


def _count_character(counts: Counter[str], line: Any) -> None:
    if not isinstance(line, dict):
        return
    character = str(line.get("character") or "").strip()
    if character and character not in _LOW_VALUE_CHARACTERS:
        counts[character] += 1


def _script_anchor_terms(payload: Dict[str, Any]) -> set[str]:
    contract = _structured_contract(payload)
    text = " ".join(
        [
            str(payload.get("content") or ""),
            str(contract.get("title") or ""),
            str(contract.get("logline") or ""),
        ]
    )
    return {
        value.casefold()
        for value in re.findall(
            r"(?<![\w-])(?:[A-Z]{2,}|[A-Za-z][A-Za-z0-9._-]{2,})(?![\w-])",
            text,
        )
        if value.casefold() not in _GENERIC_ANCHORS
    }


def _structured_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    direct = payload.get("structured_script_contract")
    if isinstance(direct, dict):
        return direct
    metadata = payload.get("metadata")
    nested = (
        metadata.get("structured_script_contract")
        if isinstance(metadata, dict)
        else None
    )
    return nested if isinstance(nested, dict) else {}


def _beat_contract_coverage(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = _structured_contract(payload)
    if not raw:
        return {
            "present": False,
            "valid": False,
            "scene_count": 0,
            "beat_count": 0,
            "action_count": 0,
            "dialogue_count": 0,
        }
    try:
        from app.services.script.beat_contract_normalizer import (
            normalize_script_beat_contract,
        )

        contract = normalize_script_beat_contract({"structured_script_contract": raw})
    except Exception as exc:
        return {
            "present": True,
            "valid": False,
            "scene_count": 0,
            "beat_count": 0,
            "action_count": 0,
            "dialogue_count": 0,
            "error": str(exc),
        }
    beats = [beat for scene in contract.scenes for beat in scene.beats]
    return {
        "present": True,
        "valid": True,
        "scene_count": len(contract.scenes),
        "beat_count": len(beats),
        "action_count": sum(len(beat.action_lines) for beat in beats),
        "dialogue_count": sum(len(beat.dialogue_lines) for beat in beats),
    }
