from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.services.script.production_hooks import (
    build_hook_schedule,
    render_production_requirements,
)

logger = get_logger(__name__)

AttemptGenerator = Callable[[int, str], Awaitable[Dict[str, Any]]]
AttemptScorer = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

PASS_OVERALL_THRESHOLD = 4.0
PASS_DIMENSION_THRESHOLD = 3.5
MAX_PRODUCTION_REWRITES = 2


@dataclass
class ProductionPipelineResult:
    selected: Dict[str, Any]
    hook_schedule: Dict[str, Any]
    attempts: List[Dict[str, Any]]
    selected_attempt: int
    review_required: bool

    def metadata(self) -> Dict[str, Any]:
        selected_scoring = _safe_dict(self.selected.get("scoring"))
        return {
            "generation_mode": "production",
            "hook_schedule": self.hook_schedule,
            "attempts": [summarize_attempt(attempt) for attempt in self.attempts],
            "selected_attempt": self.selected_attempt,
            "score": _safe_dict(selected_scoring.get("script_score")),
            "traffic_sheet": _safe_dict(selected_scoring.get("traffic_sheet")),
            "asset_tags": _safe_dict(selected_scoring.get("asset_tags")),
            "review_required": self.review_required,
        }


async def run_production_script_generation(
    *,
    story: Dict[str, Any],
    episode: Dict[str, Any],
    marketing_overrides: Optional[Dict[str, Any]],
    base_additional_requirements: Optional[str],
    generate_attempt: AttemptGenerator,
    score_attempt: AttemptScorer,
    max_rewrites: int = MAX_PRODUCTION_REWRITES,
) -> ProductionPipelineResult:
    """Run generation, scoring, and rewrite attempts; return the best attempt."""

    hook_schedule = build_hook_schedule(story, episode, marketing_overrides)
    attempts: List[Dict[str, Any]] = []
    rewrite_guidance: List[str] = []
    max_attempts = max(1, max_rewrites + 1)

    for attempt_no in range(1, max_attempts + 1):
        requirements = render_production_requirements(
            base_additional_requirements=base_additional_requirements,
            hook_schedule=hook_schedule,
            rewrite_guidance=rewrite_guidance,
            attempt_no=attempt_no,
        )
        generated = await generate_attempt(attempt_no, requirements)
        try:
            scoring = await score_attempt(generated)
        except Exception as exc:
            logger.warning("Production script scoring failed", exc_info=True)
            scoring = _default_scoring(error=str(exc))

        attempt = {
            **generated,
            "attempt": attempt_no,
            "scoring": scoring,
            "verdict": score_verdict(scoring),
            "overall_score": score_overall(scoring),
        }
        attempts.append(attempt)
        if score_passes(scoring):
            break

        rewrite_guidance = extract_rewrite_guidance(scoring)
        if not rewrite_guidance:
            rewrite_guidance = ["提高冲突强度、角色辨识度、投流可剪性和逻辑清晰度。"]

    selected = select_best_attempt(attempts)
    selected_attempt = int(selected.get("attempt") or 1)
    return ProductionPipelineResult(
        selected=selected,
        hook_schedule=hook_schedule,
        attempts=attempts,
        selected_attempt=selected_attempt,
        review_required=not score_passes(_safe_dict(selected.get("scoring"))),
    )


def score_passes(scoring: Dict[str, Any]) -> bool:
    script_score = _safe_dict(scoring.get("script_score"))
    overall = score_overall(scoring)
    dims = _safe_dict(script_score.get("dimension_scores"))
    if overall < PASS_OVERALL_THRESHOLD:
        return False
    numeric_dims = [
        float(value)
        for value in dims.values()
        if isinstance(value, (int, float)) or _looks_numeric(value)
    ]
    return bool(numeric_dims) and min(numeric_dims) >= PASS_DIMENSION_THRESHOLD


def score_verdict(scoring: Dict[str, Any]) -> str:
    script_score = _safe_dict(scoring.get("script_score"))
    verdict = script_score.get("verdict")
    if score_passes(scoring):
        return "pass"
    if verdict and verdict != "pass":
        return str(verdict)
    return "review"


def score_overall(scoring: Dict[str, Any]) -> float:
    script_score = _safe_dict(scoring.get("script_score"))
    value = script_score.get("overall_score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def extract_rewrite_guidance(scoring: Dict[str, Any]) -> List[str]:
    script_score = _safe_dict(scoring.get("script_score"))
    guidance = script_score.get("rewrite_guidance")
    if not isinstance(guidance, list):
        return []
    return [str(item).strip() for item in guidance if str(item).strip()]


def select_best_attempt(attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not attempts:
        raise RuntimeError("production_pipeline_no_attempts")
    for attempt in attempts:
        if score_passes(_safe_dict(attempt.get("scoring"))):
            return attempt
    return max(attempts, key=lambda item: float(item.get("overall_score") or 0.0))


def summarize_attempt(attempt: Dict[str, Any]) -> Dict[str, Any]:
    result = _safe_dict(attempt.get("result"))
    scoring = _safe_dict(attempt.get("scoring"))
    quality_gate = _safe_dict(result.get("quality_gate"))
    return {
        "attempt": attempt.get("attempt"),
        "verdict": attempt.get("verdict"),
        "overall_score": attempt.get("overall_score"),
        "generation_method": result.get("generation_method"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "quality_gate": {
            "passed": quality_gate.get("passed"),
            "failed_checks": quality_gate.get("failed_checks"),
        }
        if quality_gate
        else None,
        "score": _safe_dict(scoring.get("script_score")),
        "asset_tags": _safe_dict(scoring.get("asset_tags")),
    }


def _default_scoring(*, error: Optional[str] = None) -> Dict[str, Any]:
    return {
        "script_score": {
            "overall_score": 0.0,
            "verdict": "review",
            "risks": [error or "scoring_failed"],
            "rewrite_guidance": ["重新强化冲突、爽点、卡点和投流可剪性。"],
        },
        "traffic_sheet": {"assets": []},
        "asset_tags": {"asset_count": 0, "hook_types": [], "durations": []},
    }


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _looks_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
