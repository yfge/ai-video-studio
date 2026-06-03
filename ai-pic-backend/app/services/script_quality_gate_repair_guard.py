from __future__ import annotations

from typing import Any, Dict


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
    passed = not lost_fields and not content_too_short
    return (
        passed,
        {
            "passed": passed,
            "before": before_counts,
            "after": repaired_counts,
            "lost_fields": lost_fields,
            "content_too_short": content_too_short,
        },
    )


def _script_structure_counts(payload: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for field in ("scenes", "dialogues", "stage_directions"):
        value = payload.get(field)
        counts[field] = len(value) if isinstance(value, list) else 0
    counts["content_chars"] = len(str(payload.get("content") or ""))
    return counts
