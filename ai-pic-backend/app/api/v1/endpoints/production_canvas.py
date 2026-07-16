from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasRunActionRequest,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
)
from app.schemas.production_canvas_review import (
    ProductionCanvasCandidateApprovalRequest,
    ProductionCanvasCandidateBranchRequest,
    ProductionCanvasCandidateRejectionRequest,
    ProductionCanvasTimelinePlacementRequest,
)
from app.services.production_canvas import (
    approve_canvas_media_candidate,
    attach_canvas_run,
    branch_canvas_media_candidate,
    build_autonomous_canvas_skill_plan,
    control_canvas_run,
    execute_canvas_skill,
    list_canvas_media_candidates,
    load_canvas_skill_run,
    persist_canvas_skill_run,
    place_canvas_video_in_timeline,
    reject_canvas_media_candidate,
    save_canvas_client_state,
    save_canvas_execution_response,
)
from app.services.production_canvas.access_control import (
    require_canvas_access,
    require_canvas_access_if_run_exists,
)
from app.services.production_canvas.graph_runtime import evaluate_canvas_graph
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


def _candidate_http_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    if code == "canvas_access_forbidden":
        return HTTPException(status_code=403, detail=code)
    status = 404 if code.endswith("not_found") else 409
    return HTTPException(status_code=status, detail=code)


def _run_action_http_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    if code == "canvas_access_forbidden":
        return HTTPException(status_code=403, detail=code)
    status = 404 if code.endswith("not_found") else 409
    return HTTPException(status_code=status, detail=code)


@router.post("/plan", response_model=dict)
async def create_production_canvas_plan(
    request: ProductionCanvasPlanRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    plan: ProductionCanvasPlanResponse = await build_autonomous_canvas_skill_plan(
        db,
        current_user,
        request,
    )
    task = persist_canvas_skill_run(db, current_user, request, plan)
    plan = attach_canvas_run(plan, task)
    return {"success": True, "data": plan.model_dump(by_alias=True)}


@router.post("/execute", response_model=dict)
async def execute_production_canvas_skill(
    request: ProductionCanvasSkillExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if request.run_id:
        try:
            require_canvas_access_if_run_exists(
                db,
                current_user,
                request.run_id,
                "approve" if request.skill == "timeline.place" else "execute",
            )
        except ValueError as exc:
            raise _run_action_http_error(exc) from exc
    result: ProductionCanvasSkillExecuteResponse = execute_canvas_skill(
        db,
        current_user,
        request,
    )
    if request.run_id:
        save_canvas_execution_response(db, current_user, request.run_id, result)
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


@router.post("/runs/{run_id}/actions", response_model=dict)
async def control_production_canvas_run(
    run_id: str,
    request: ProductionCanvasRunActionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "execute")
        result = control_canvas_run(db, current_user, run_id, request)
    except ValueError as exc:
        raise _run_action_http_error(exc) from exc
    return {"success": True, "data": result.model_dump(by_alias=True)}


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


@router.get("/runs/{run_id}/nodes/{node_id}/candidates", response_model=dict)
async def get_production_canvas_media_candidates(
    run_id: str,
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        result = list_canvas_media_candidates(db, current_user, run_id, node_id)
    except ValueError as exc:
        raise _candidate_http_error(exc) from exc
    return {"success": True, "data": result.model_dump()}


@router.post("/runs/{run_id}/nodes/{node_id}/approval", response_model=dict)
async def approve_production_canvas_media_candidate(
    run_id: str,
    node_id: str,
    request: ProductionCanvasCandidateApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "approve")
        run = approve_canvas_media_candidate(
            db, current_user, run_id, node_id, request.candidate_id
        )
    except ValueError as exc:
        raise _candidate_http_error(exc) from exc
    return {"success": True, "data": run.model_dump(by_alias=True)}


@router.post("/runs/{run_id}/nodes/{node_id}/rejection", response_model=dict)
async def reject_production_canvas_media_candidate(
    run_id: str,
    node_id: str,
    request: ProductionCanvasCandidateRejectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "approve")
        run = reject_canvas_media_candidate(
            db,
            current_user,
            run_id,
            node_id,
            request.candidate_id,
            request.reason,
        )
    except ValueError as exc:
        raise _candidate_http_error(exc) from exc
    return {"success": True, "data": run.model_dump(by_alias=True)}


@router.post("/runs/{run_id}/nodes/{node_id}/branches", response_model=dict)
async def branch_production_canvas_media_candidate(
    run_id: str,
    node_id: str,
    request: ProductionCanvasCandidateBranchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "execute")
        run = branch_canvas_media_candidate(db, current_user, run_id, node_id, request)
    except ValueError as exc:
        raise _candidate_http_error(exc) from exc
    return {"success": True, "data": run.model_dump(by_alias=True)}


@router.post("/runs/{run_id}/nodes/{node_id}/timeline-placement", response_model=dict)
async def place_production_canvas_video_in_timeline(
    run_id: str,
    node_id: str,
    request: ProductionCanvasTimelinePlacementRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "approve")
        run = place_canvas_video_in_timeline(db, current_user, run_id, node_id, request)
    except ValueError as exc:
        raise _candidate_http_error(exc) from exc
    return {"success": True, "data": run.model_dump(by_alias=True)}


@router.put("/runs/{run_id}/state", response_model=dict)
async def save_production_canvas_run_state(
    run_id: str,
    request: ProductionCanvasSavedState,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        require_canvas_access(db, current_user, run_id, "edit")
    except ValueError as exc:
        raise _run_action_http_error(exc) from exc
    run = save_canvas_client_state(db, current_user, run_id, request)
    if run is None:
        raise HTTPException(status_code=404, detail="Production canvas run not found")
    return {"success": True, "data": run.model_dump(by_alias=True)}
