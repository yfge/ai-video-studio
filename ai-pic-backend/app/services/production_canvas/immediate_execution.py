from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas.asset_selection import select_canvas_assets
from app.services.production_canvas.execution_common import skill_definition
from sqlalchemy.orm import Session


def _asset_names(assets) -> str:
    return "、".join(asset.name for asset in assets)


def execute_brief_compose(
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("brief.compose")
    brief = request.production_context.brief if request.production_context else None
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill="brief.compose",
            label=skill.label if skill else "Brief Skill",
            status=(
                "review" if brief is None or brief.ready_for_execution else "blocked"
            ),
            title="已确认结构化 Production Brief",
            detail=(
                f"目标：{brief.intent.objective}"
                if brief
                else f"目标：{request.prompt}"
            ),
            outputs={
                "production_brief": (
                    brief.model_dump() if brief else {"source_prompt": request.prompt}
                ),
                "prompt": request.prompt,
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        )
    )


def execute_content_planning(
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("content.plan")
    context = request.production_context
    if context is None:
        return ProductionCanvasSkillExecuteResponse(
            skill_result=ProductionCanvasSkillResult(
                skill="content.plan",
                label=skill.label if skill else "Content Planning",
                status="blocked",
                title="内容规划等待 Production Brief",
                detail="需要先完成结构化意图与参数解析。",
                outputs={"required_inputs": ["production_context"]},
                reuse_targets=skill.reuse_targets if skill else [],
            )
        )
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill="content.plan",
            label=skill.label if skill else "Content Planning",
            status="review" if context.brief.ready_for_execution else "blocked",
            title=f"内容规划：{context.content_plan.title}",
            detail=(
                f"已规划 {len(context.content_plan.episodes)} 集，"
                f"持续机制：{context.content_plan.recurring_engine}"
            ),
            outputs={"production_context": context.model_dump()},
            reuse_targets=skill.reuse_targets if skill else [],
        )
    )


def execute_asset_selection(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("asset.select")
    selection = select_canvas_assets(db, user, request)
    ip_names = _asset_names(selection.selected.virtual_ips) or "待选择 IP"
    env_names = _asset_names(selection.selected.environments) or "待选择环境"
    status = (
        "review"
        if selection.selected.virtual_ips or selection.selected.environments
        else "blocked"
    )
    outputs = selection.outputs()
    if request.production_context:
        outputs["production_context"] = request.production_context.model_dump()
    if status == "blocked":
        outputs["required_inputs"] = ["virtual_ip_id", "environment_id"]
    if request.run_id:
        outputs["canvas_run_id"] = request.run_id
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill="asset.select",
            label=skill.label if skill else "Asset Selection",
            status=status,
            title=f"复用资产：{ip_names} / {env_names}",
            detail=f"复用现有 IP：{ip_names}；环境：{env_names}",
            outputs=outputs,
            reuse_targets=skill.reuse_targets if skill else [],
        )
    )
