from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.schemas.generation import StoryOutlineModel
from app.services.story.story_outline_character_validation import (
    story_outline_validation_passed,
    validate_story_outline_characters,
)
from app.services.story.story_outline_quality import validate_story_outline_quality
from app.services.story_quality_gate import evaluate_story_quality_gate

logger = logging.getLogger(__name__)

_STORY_CONTRACT_FIELDS = (
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


@dataclass
class StoryOutlineValidation:
    passed: bool
    char_validation: dict[str, Any]
    quality_validation: dict[str, Any]
    quality_gate: dict[str, Any] | None
    quality_gate_issues: list[str]
    quality_gate_issue_details: list[str]
    story_quality_warnings: list[str]
    character_warnings: list[str]


def story_outline_schema(*, production_mode: bool) -> dict[str, Any]:
    schema = StoryOutlineModel.model_json_schema()
    if not production_mode:
        return schema

    schema = deepcopy(schema)
    required = schema.setdefault("required", [])
    if "structured_story_contract" not in required:
        required.append("structured_story_contract")

    schema.setdefault("properties", {})["structured_story_contract"] = {
        "type": "object",
        "description": "生产级短剧故事合同；production 生成必须完整返回。",
        "required": list(_STORY_CONTRACT_FIELDS),
        "additionalProperties": True,
        "properties": _story_contract_schema_properties(),
    }
    return schema


def validate_story_outline_candidate(
    parsed: dict[str, Any],
    *,
    characters: list[dict[str, Any]],
    hook_plan: dict[str, Any] | None,
    content_restrictions: list[str] | None,
    production_mode: bool,
    log_suffix: str,
) -> StoryOutlineValidation:
    StoryOutlineModel.model_validate(parsed)
    char_validation = validate_story_outline_characters(parsed, characters)
    if char_validation["character_warnings"]:
        logger.warning(
            "Story character validation warnings%s",
            log_suffix,
            extra={"warnings": char_validation["character_warnings"]},
        )

    quality_validation = validate_story_outline_quality(
        parsed, hook_plan, content_restrictions
    )
    if quality_validation["story_quality_warnings"]:
        logger.warning(
            "Story quality validation warnings%s",
            log_suffix,
            extra={"warnings": quality_validation["story_quality_warnings"]},
        )

    quality_gate = None
    quality_gate_issues: list[str] = []
    quality_gate_issue_details: list[str] = []
    if production_mode:
        quality_gate = evaluate_story_quality_gate(
            story=parsed,
            hook_plan=hook_plan,
            content_restrictions=content_restrictions,
            require_story_contract=True,
        )
        quality_gate_issues = _quality_gate_issue_ids(quality_gate)
        quality_gate_issue_details = _quality_gate_issue_details(quality_gate)
        if not quality_gate.get("passed"):
            logger.warning(
                "Story production quality gate warnings%s",
                log_suffix,
                extra={"issues": quality_gate_issue_details},
            )

    passed = story_outline_validation_passed(char_validation, quality_validation) and (
        not production_mode or bool(quality_gate and quality_gate.get("passed"))
    )
    return StoryOutlineValidation(
        passed=passed,
        char_validation=char_validation,
        quality_validation=quality_validation,
        quality_gate=quality_gate,
        quality_gate_issues=quality_gate_issues,
        quality_gate_issue_details=quality_gate_issue_details,
        story_quality_warnings=quality_validation["story_quality_warnings"],
        character_warnings=char_validation["character_warnings"],
    )


def build_story_agent_result(
    *,
    latest_text: str,
    parsed: dict[str, Any],
    resolved_template: str,
    provider_used: str | None,
    model_used: str | None,
    usage: dict[str, Any] | None,
    prompt: str,
    generation_mode: str,
    production_mode: bool,
    reasoning: list[str],
    validation: StoryOutlineValidation,
) -> dict[str, Any]:
    return {
        "content": latest_text,
        "normalized": parsed,
        "generation_method": "langgraph_story",
        "template_used": resolved_template,
        "provider_used": provider_used,
        "model_used": model_used,
        "usage": usage,
        "prompt": prompt,
        "generation_mode": generation_mode,
        "production_mode": production_mode,
        "prompt_version": resolved_template,
        "contract_version": "story_contract_v1",
        "reasoning": reasoning,
        "quality_gate": validation.quality_gate,
        **validation.char_validation,
        **validation.quality_validation,
    }


def _story_contract_schema_properties() -> dict[str, Any]:
    return {
        "target_audience": {"type": "string"},
        "core_emotional_pain": {"type": "string"},
        "big_expectation": {"type": "string"},
        "small_expectation_ladder": _string_array_schema(),
        "protagonist_goal": {"type": "string"},
        "structural_conflict": {"type": "string"},
        "information_gap": {"type": "string"},
        "first_three_episode_spine": {"type": "string"},
        "stage_highs": _string_array_schema(),
        "shootability": {"type": "string"},
        "compliance_risks": {"type": "array", "items": {"type": "string"}},
        "traffic_hooks": _string_array_schema(),
    }


def _string_array_schema() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}, "minItems": 1}


def _quality_gate_issue_ids(quality_gate: dict[str, Any] | None) -> list[str]:
    return [
        str(issue.get("id") or issue.get("message") or "unknown_quality_issue")
        for issue in _quality_gate_issues(quality_gate)
    ]


def _quality_gate_issue_details(quality_gate: dict[str, Any] | None) -> list[str]:
    details: list[str] = []
    for issue in _quality_gate_issues(quality_gate):
        issue_id = issue.get("id") or "quality_issue"
        message = issue.get("message") or ""
        issue_details = issue.get("details") or {}
        details.append(f"{issue_id}: {message}; details={issue_details}")
    return details


def _quality_gate_issues(quality_gate: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not quality_gate:
        return []
    issues = (quality_gate.get("blocking_issues") or []) + (
        quality_gate.get("warnings") or []
    )
    return [issue for issue in issues if isinstance(issue, dict)]
