from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.production_canvas_collaboration import (
    ProductionCanvasCollaboratorRequest,
    ProductionCanvasCommentRequest,
)
from app.services.production_canvas.collaboration import (
    add_canvas_comment,
    load_canvas_collaboration,
    remove_canvas_collaborator,
    upsert_canvas_collaborator,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


def _collaboration_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    if code == "canvas_access_forbidden":
        return HTTPException(status_code=403, detail=code)
    status = 404 if code.endswith("not_found") else 409
    return HTTPException(status_code=status, detail=code)


@router.get("/runs/{run_id}/collaboration", response_model=dict)
async def get_production_canvas_collaboration(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        result = load_canvas_collaboration(db, current_user, run_id)
    except ValueError as exc:
        raise _collaboration_error(exc) from exc
    return {"success": True, "data": result.model_dump(mode="json")}


@router.put("/runs/{run_id}/collaborators", response_model=dict)
async def put_production_canvas_collaborator(
    run_id: str,
    request: ProductionCanvasCollaboratorRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        result = upsert_canvas_collaborator(db, current_user, run_id, request)
    except ValueError as exc:
        raise _collaboration_error(exc) from exc
    return {"success": True, "data": result.model_dump(mode="json")}


@router.delete("/runs/{run_id}/collaborators/{collaborator_id}", response_model=dict)
async def delete_production_canvas_collaborator(
    run_id: str,
    collaborator_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        result = remove_canvas_collaborator(db, current_user, run_id, collaborator_id)
    except ValueError as exc:
        raise _collaboration_error(exc) from exc
    return {"success": True, "data": result.model_dump(mode="json")}


@router.post("/runs/{run_id}/comments", response_model=dict)
async def post_production_canvas_comment(
    run_id: str,
    request: ProductionCanvasCommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        result = add_canvas_comment(db, current_user, run_id, request)
    except ValueError as exc:
        raise _collaboration_error(exc) from exc
    return {"success": True, "data": result.model_dump(mode="json")}
