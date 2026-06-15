from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.quality_gate_core import build_quality_gate_report, make_quality_check
from app.services.story.story_outline_quality import validate_story_outline_quality

STORY_CONTRACT_VERSION = "story_contract_v1"

_REQUIRED_STORY_CONTRACT_FIELDS = (
    "target_audience",
    "core_emotional_pain",
    "big_expectation",
    "small_expectation_ladder",
    "protagonist_goal",
    "structural_conflict",
    "information_gap",
    "first_three_episode_spine",
    "stage_highs",
    "shootability",
    "compliance_risks",
    "traffic_hooks",
)


def evaluate_story_quality_gate(
    *,
    story: Dict[str, Any],
    hook_plan: Optional[Dict[str, Any]] = None,
    content_restrictions: Optional[list[str]] = None,
    require_story_contract: bool = False,
) -> Dict[str, Any]:
    checks: list[Dict[str, Any]] = [
        make_quality_check(
            "story_non_empty",
            bool(story.get("premise") and story.get("synopsis")),
            "story premise and synopsis must not be empty",
        )
    ]

    quality = validate_story_outline_quality(story, hook_plan, content_restrictions)
    checks.append(
        make_quality_check(
            "story_outline_quality",
            quality.get("story_quality_passed", True),
            "story outline quality validator must pass",
            details=quality.get("story_quality_result") or {},
        )
    )

    if require_story_contract:
        checks.append(required_story_contract_check(story))

    contract = _story_contract(story)
    if contract:
        checks.append(story_contract_quality_check(contract))

    return build_quality_gate_report(kind="story", checks=checks)


def required_story_contract_check(story: Dict[str, Any]) -> Dict[str, Any]:
    return make_quality_check(
        "structured_story_contract_required",
        bool(_story_contract(story)),
        "production story generation must return structured_story_contract",
        details={"required": True, "version": STORY_CONTRACT_VERSION},
    )


def story_contract_quality_check(contract: Dict[str, Any]) -> Dict[str, Any]:
    missing = [
        field
        for field in _REQUIRED_STORY_CONTRACT_FIELDS
        if not _has_required_contract_field(contract, field)
    ]
    compliance_risks = contract.get("compliance_risks")
    has_blocking_risk = isinstance(compliance_risks, list) and any(
        str(item).strip() for item in compliance_risks
    )
    passed = not missing and not has_blocking_risk
    return make_quality_check(
        "structured_story_contract",
        passed,
        "structured_story_contract must define audience, expectation, conflict, shootability, and traffic hooks",
        details={
            "missing_fields": missing,
            "compliance_risks": compliance_risks if has_blocking_risk else [],
            "version": STORY_CONTRACT_VERSION,
        },
    )


def _story_contract(story: Dict[str, Any]) -> Dict[str, Any]:
    raw = story.get("structured_story_contract")
    if isinstance(raw, dict):
        return raw
    metadata = story.get("metadata")
    if isinstance(metadata, dict) and isinstance(
        metadata.get("structured_story_contract"), dict
    ):
        return metadata["structured_story_contract"]
    return {}


def _has_contract_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return value is not None


def _has_required_contract_field(contract: Dict[str, Any], field: str) -> bool:
    if field == "compliance_risks":
        return field in contract and isinstance(contract.get(field), list)
    return _has_contract_value(contract.get(field))
