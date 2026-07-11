from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
)
from app.services.production_canvas import (
    attach_canvas_run,
    build_canvas_skill_plan,
    execute_canvas_skill,
    load_canvas_skill_run,
    persist_canvas_skill_run,
    save_canvas_skill_result,
    save_canvas_state,
)
from app.services.production_canvas.graph_runtime import evaluate_canvas_graph
from fastapi import APIRouter, Depends, HTTPException
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
    if request.run_id:
        save_canvas_skill_result(db, current_user, request.run_id, result.skill_result)
    return {"success": True, "data": result.model_dump()}


@router.get("/runs/{run_id}", response_model=dict)
async def get_production_canvas_run(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    run = load_canvas_skill_run(db, current_user, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Production canvas run not found")
    return {"success": True, "data": run.model_dump(by_alias=True)}


@router.get("/runs/{run_id}/graph", response_model=dict)
async def get_production_canvas_graph(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    run = load_canvas_skill_run(db, current_user, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Production canvas run not found")
    if run.saved_state is None:
        raise HTTPException(status_code=409, detail="Production canvas graph not saved")
    evaluation = evaluate_canvas_graph(run.saved_state)
    return {"success": True, "data": evaluation.model_dump()}


@router.put("/runs/{run_id}/state", response_model=dict)
async def save_production_canvas_run_state(
    run_id: str,
    request: ProductionCanvasSavedState,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    run = save_canvas_state(db, current_user, run_id, request)
    if run is None:
        raise HTTPException(status_code=404, detail="Production canvas run not found")
    return {"success": True, "data": run.model_dump(by_alias=True)}
