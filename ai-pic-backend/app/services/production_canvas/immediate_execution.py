from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas.asset_selection import select_canvas_assets
from app.services.production_canvas.execution_common import skill_definition


def _asset_names(assets) -> str:
    return "、".join(asset.name for asset in assets)


def execute_brief_compose(
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("brief.compose")
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill="brief.compose",
            label=skill.label if skill else "Brief Skill",
            status="ready",
            title="已确认生产 brief",
            detail=f"目标：{request.prompt}",
            outputs={
                "prompt": request.prompt,
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
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
