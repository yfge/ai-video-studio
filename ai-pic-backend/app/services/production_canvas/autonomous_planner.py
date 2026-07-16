from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.production_canvas import (
    ProductionCanvasResolvedContext,
    ProductionCanvasSavedEdge,
    ProductionCanvasSelectedAssets,
)
from app.schemas.production_canvas_planner import (
    ProductionCanvasPlannerEvidence,
    ProductionCanvasPlannerProposal,
)
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service

from .planner_contracts import (
    canonical_canvas_planner_proposal,
    compile_canvas_planner_edges,
)
from .planner_ports import planner_skill_catalog
from .skills import list_canvas_skill_definitions

logger = logging.getLogger(__name__)
_DEFAULT_MANAGER = object()


@dataclass(frozen=True)
class CanvasPlannerDecision:
    proposal: ProductionCanvasPlannerProposal
    edges: list[ProductionCanvasSavedEdge]
    evidence: ProductionCanvasPlannerEvidence

    @property
    def selected_skills(self) -> list[str]:
        return [step.skill for step in self.proposal.steps]


def _validation_errors(payload: dict) -> list[dict] | None:
    try:
        compile_canvas_planner_edges(
            ProductionCanvasPlannerProposal.model_validate(payload)
        )
    except ValueError as exc:
        return [{"loc": ["steps"], "msg": str(exc), "type": "value_error"}]
    return None


def _error_messages(errors: list[dict] | None) -> list[str]:
    messages = []
    for error in errors or []:
        location = ".".join(str(item) for item in error.get("loc") or [])
        message = str(error.get("msg") or "invalid planner proposal")
        messages.append(f"{location}: {message}" if location else message)
    return messages[:8]


def _attempt_metadata(result: dict) -> tuple[str | None, str | None]:
    attempts = [
        result.get("first_attempt"),
        *(result.get("repair_attempts") or []),
    ]
    valid = next(
        (
            attempt
            for attempt in reversed(attempts)
            if isinstance(attempt, dict) and attempt.get("normalized") is not None
        ),
        None,
    )
    attempt = valid or next(
        (item for item in attempts if isinstance(item, dict)),
        {},
    )
    return attempt.get("provider_used"), attempt.get("model_used")


def deterministic_canvas_planner_decision(
    objective: str,
    *,
    reason: str,
    validation_errors: list[str] | None = None,
    repair_count: int = 0,
    provider: str | None = None,
    model: str | None = None,
) -> CanvasPlannerDecision:
    proposal = canonical_canvas_planner_proposal(objective)
    return CanvasPlannerDecision(
        proposal=proposal,
        edges=compile_canvas_planner_edges(proposal),
        evidence=ProductionCanvasPlannerEvidence(
            mode="deterministic_fallback",
            objective=objective,
            selected_skills=[step.skill for step in proposal.steps],
            rationale=[f"{step.skill}: {step.reason}" for step in proposal.steps],
            assumptions=proposal.assumptions,
            warnings=["自主规划不可用，已采用经过验证的确定性完整方案。"],
            validation_errors=validation_errors or [],
            provider=provider,
            model=model,
            repair_count=min(repair_count, 1),
            fallback_reason=reason,
        ),
    )


def _catalog_json() -> str:
    definitions = {item.id: item for item in list_canvas_skill_definitions()}
    catalog = []
    for contract in planner_skill_catalog():
        definition = definitions[contract["id"]]
        catalog.append(
            {
                **contract,
                "label": definition.label,
                "description": definition.description,
            }
        )
    return json.dumps(catalog, ensure_ascii=False)


async def plan_canvas_skills(
    *,
    prompt: str,
    resolved_context: ProductionCanvasResolvedContext,
    selected_assets: ProductionCanvasSelectedAssets,
    ai_manager: Any = _DEFAULT_MANAGER,
) -> CanvasPlannerDecision:
    manager = ai_service.ai_manager if ai_manager is _DEFAULT_MANAGER else ai_manager
    if manager is None:
        return deterministic_canvas_planner_decision(
            prompt, reason="ai_manager_unavailable"
        )
    try:
        base_prompt = prompt_manager.render_prompt(
            "production_canvas_planner",
            {
                "prompt": prompt,
                "context_json": json.dumps(
                    resolved_context.model_dump(exclude_none=True),
                    ensure_ascii=False,
                ),
                "selected_assets_json": json.dumps(
                    selected_assets.model_dump(),
                    ensure_ascii=False,
                ),
                "skill_catalog_json": _catalog_json(),
            },
        )
        result = await generate_with_repair(
            ai_manager=manager,
            base_prompt=base_prompt,
            model=None,
            prefer_provider=None,
            temperature=0.1,
            schema_name="production_canvas_plan",
            schema=ProductionCanvasPlannerProposal.model_json_schema(),
            system_prompt=prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value,
                {},
            ),
            pydantic_model=ProductionCanvasPlannerProposal,
            extra_validator=_validation_errors,
            max_repairs=1,
            max_tokens=1800,
            stream=False,
        )
    except Exception as exc:
        logger.warning("Production canvas planner failed: %s", type(exc).__name__)
        return deterministic_canvas_planner_decision(
            prompt,
            reason=f"planner_exception:{type(exc).__name__}",
        )

    provider, model = _attempt_metadata(result)
    repair_count = len(result.get("repair_attempts") or [])
    normalized = result.get("normalized")
    if normalized is None:
        first = result.get("first_attempt") or {}
        reason = "provider_error" if not first.get("success") else "invalid_plan"
        return deterministic_canvas_planner_decision(
            prompt,
            reason=reason,
            validation_errors=_error_messages(result.get("validation_errors")),
            repair_count=repair_count,
            provider=provider,
            model=model,
        )

    proposal = ProductionCanvasPlannerProposal.model_validate(normalized)
    edges = compile_canvas_planner_edges(proposal)
    return CanvasPlannerDecision(
        proposal=proposal,
        edges=edges,
        evidence=ProductionCanvasPlannerEvidence(
            mode="autonomous",
            objective=proposal.objective,
            selected_skills=[step.skill for step in proposal.steps],
            rationale=[f"{step.skill}: {step.reason}" for step in proposal.steps],
            assumptions=proposal.assumptions,
            provider=provider,
            model=model,
            repair_count=repair_count,
        ),
    )
