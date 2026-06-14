from __future__ import annotations

from typing import Any, Dict, List

from app.services.quality_gate_core import build_quality_gate_report, make_quality_check
from app.services.script_score_thresholds import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
)


def build_production_quality_gate(
    *,
    attempt_summaries: List[Dict[str, Any]],
    scores: List[Dict[str, Any]],
    selected_score: Dict[str, Any],
    selected_attempt: int,
    rewrite_guidance: List[str],
    score: float,
) -> Dict[str, Any]:
    details = {
        "thresholds": {
            "overall": PASS_OVERALL_THRESHOLD,
            "dimension": PASS_DIMENSION_THRESHOLD,
        },
        "selected_attempt": selected_attempt,
        "attempts": attempt_summaries,
        "scores": scores,
        "selected_score": selected_score,
        "rewrite_guidance": rewrite_guidance,
    }
    return build_quality_gate_report(
        kind="script",
        checks=[
            make_quality_check(
                "production_script_score",
                False,
                "production script score must pass strict thresholds",
                score=score,
                details=details,
            )
        ],
    )
