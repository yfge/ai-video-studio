from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasSkillResult,
)
from app.schemas.production_canvas_content import ProductionCanvasProductionContext
from app.services.production_canvas.asset_selection import CanvasAssetSelection
from app.services.production_canvas.runner_contract import (
    asset_detail,
    asset_status,
    asset_title,
    downstream_detail,
    downstream_outputs,
    downstream_status,
    required_inputs,
)
from app.services.production_canvas.skills import list_canvas_skill_definitions


def build_canvas_skill_results(
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    context: ProductionCanvasProductionContext,
) -> list[ProductionCanvasSkillResult]:
    asset_outputs = {
        **selection.outputs(),
        "planning_mode": request.planning_mode,
        "production_context": context.model_dump(),
    }
    results: list[ProductionCanvasSkillResult] = []
    for skill in list_canvas_skill_definitions():
        if skill.id == "brief.compose":
            results.append(
                ProductionCanvasSkillResult(
                    skill=skill.id,
                    label=skill.label,
                    status=(
                        "review" if context.brief.ready_for_execution else "blocked"
                    ),
                    title="已解析生产意图、参数、模型与规格",
                    detail=(
                        f"目标：{context.brief.intent.objective}"
                        if context.brief.ready_for_execution
                        else "存在必须由用户补充的生产信息。"
                    ),
                    outputs={
                        "production_brief": context.brief.model_dump(),
                        "prompt": context.brief.source_prompt,
                        "planning_mode": request.planning_mode,
                    },
                    reuse_targets=skill.reuse_targets,
                )
            )
            continue
        if skill.id == "content.plan":
            results.append(
                ProductionCanvasSkillResult(
                    skill=skill.id,
                    label=skill.label,
                    status=(
                        "review" if context.brief.ready_for_execution else "blocked"
                    ),
                    title=f"内容规划：{context.content_plan.title}",
                    detail=(
                        f"{len(context.content_plan.episodes)} 集规划；"
                        f"持续机制：{context.content_plan.recurring_engine}"
                    ),
                    outputs={"production_context": context.model_dump()},
                    reuse_targets=skill.reuse_targets,
                )
            )
            continue
        if skill.id == "asset.select":
            results.append(
                ProductionCanvasSkillResult(
                    skill=skill.id,
                    label=skill.label,
                    status=asset_status(selection, context),
                    title=asset_title(selection, context),
                    detail=asset_detail(selection, context),
                    outputs=asset_outputs,
                    reuse_targets=skill.reuse_targets,
                )
            )
            continue
        outputs = downstream_outputs(request, selection, context, skill.id)
        missing_inputs = required_inputs(request, selection, skill.id, context)
        if missing_inputs:
            outputs["required_inputs"] = missing_inputs
        results.append(
            ProductionCanvasSkillResult(
                skill=skill.id,
                label=skill.label,
                status=downstream_status(request, selection, skill.id, context),
                title=skill.description,
                detail=downstream_detail(request, selection, skill.id, context),
                outputs=outputs,
                reuse_targets=skill.reuse_targets,
            )
        )
    return results
