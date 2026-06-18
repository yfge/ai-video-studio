from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
)
from app.services.production_canvas import (
    attach_canvas_run,
    build_canvas_skill_plan,
    execute_canvas_skill,
    persist_canvas_skill_run,
)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/plan", response_model=dict)
async def create_production_canvas_plan(
    request: ProductionCanvasPlanRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    plan: ProductionCanvasPlanResponse = build_canvas_skill_plan(
        db,
        current_user,
        request,
    )
    task = persist_canvas_skill_run(db, current_user, request, plan)
    plan = attach_canvas_run(plan, task)
    return {"success": True, "data": plan.model_dump()}


@router.post("/execute", response_model=dict)
async def execute_production_canvas_skill(
    request: ProductionCanvasSkillExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    result: ProductionCanvasSkillExecuteResponse = execute_canvas_skill(
        db,
        current_user,
        request,
    )
    return {"success": True, "data": result.model_dump()}
