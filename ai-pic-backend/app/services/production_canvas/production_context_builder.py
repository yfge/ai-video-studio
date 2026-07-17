from __future__ import annotations

import json
import logging
from typing import Any

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service

from .production_context_defaults import deterministic_planning_draft
from .production_context_inputs import (
    apply_answers,
    apply_explicit_content_overrides,
    finalize_questions,
)
from .production_model_selection import select_production_models

logger = logging.getLogger(__name__)
_DEFAULT_MANAGER = object()


async def build_production_planning_draft(
    request: ProductionCanvasPlanRequest,
    *,
    ai_manager: Any = _DEFAULT_MANAGER,
) -> ProductionCanvasPlanningDraft:
    manager = ai_service.ai_manager if ai_manager is _DEFAULT_MANAGER else ai_manager
    generated = await _generate_draft(request, manager)
    draft = generated or deterministic_planning_draft(
        request,
        interpretation_status="failed",
        interpretation_warnings=[
            "结构化意图模型未返回可验证的 Production Brief 和 Content Plan；"
            "本次仅保留原始目标，已阻止下游 Skill 执行。请重试规划。"
        ],
    )
    if generated is not None:
        draft = draft.model_copy(
            update={
                "brief": draft.brief.model_copy(
                    update={
                        "interpretation_status": "model_parsed",
                        "interpretation_warnings": [],
                    }
                )
            }
        )
    draft = _bind_source_prompt(draft, request.prompt)
    draft = apply_explicit_content_overrides(draft, request)
    draft = apply_answers(draft, request.clarification_answers)
    models, model_questions = await select_production_models(
        draft.brief.models,
        manager,
    )
    brief = draft.brief.model_copy(update={"models": models})
    draft = draft.model_copy(update={"brief": brief})
    return finalize_questions(draft, request, model_questions)


def build_deterministic_production_planning_draft(
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    draft = _bind_source_prompt(
        deterministic_planning_draft(request),
        request.prompt,
    )
    draft = apply_explicit_content_overrides(draft, request)
    draft = apply_answers(draft, request.clarification_answers)
    return finalize_questions(draft, request, [])


async def _generate_draft(
    request: ProductionCanvasPlanRequest,
    manager: Any,
) -> ProductionCanvasPlanningDraft | None:
    if manager is None:
        return None
    try:
        base_prompt = prompt_manager.render_prompt(
            "production_canvas_context",
            {
                "prompt": request.prompt,
                "planning_mode": request.planning_mode,
                "overrides_json": json.dumps(
                    request.brief_overrides.model_dump(exclude_none=True),
                    ensure_ascii=False,
                ),
                "answers_json": json.dumps(
                    request.clarification_answers,
                    ensure_ascii=False,
                ),
            },
        )
        result = await generate_with_repair(
            ai_manager=manager,
            base_prompt=base_prompt,
            model=request.brief_overrides.text_model,
            prefer_provider=None,
            temperature=0.35,
            schema_name="production_canvas_context",
            schema=ProductionCanvasPlanningDraft.model_json_schema(),
            system_prompt=prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value,
                {},
            ),
            pydantic_model=ProductionCanvasPlanningDraft,
            max_repairs=1,
            max_tokens=6000,
            stream=False,
        )
    except Exception as exc:
        logger.warning("Production context planning failed: %s", type(exc).__name__)
        return None
    normalized = result.get("normalized")
    if normalized is None:
        logger.warning(
            "Production context output failed validation: %s",
            result.get("validation_errors"),
        )
    return (
        ProductionCanvasPlanningDraft.model_validate(normalized)
        if normalized is not None
        else None
    )


def _bind_source_prompt(
    draft: ProductionCanvasPlanningDraft,
    prompt: str,
) -> ProductionCanvasPlanningDraft:
    brief = draft.brief.model_copy(update={"source_prompt": prompt})
    assets = brief.assets.model_copy()
    if not assets.virtual_ip_name and draft.content_plan.characters:
        candidate = draft.content_plan.characters[0].name.strip()
        if candidate not in {"主角", "主人公", "protagonist"}:
            assets.virtual_ip_name = candidate
    if not assets.environment_names and draft.content_plan.environments:
        assets.environment_names = [
            item.name for item in draft.content_plan.environments
        ]
    return draft.model_copy(
        update={"brief": brief.model_copy(update={"assets": assets})}
    )
