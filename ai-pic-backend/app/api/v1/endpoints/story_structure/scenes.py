"""
Story Structure scene endpoints.

Scene CRUD and structure operations.
"""

from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.story_structure import (
    SceneBeatResponse,
    SceneCreate,
    SceneResponse,
    SceneUpdate,
    SceneWithChildren,
    ScriptStructureResponse,
    ShotResponse,
)
from app.services import story_structure_service as svc
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/scripts/{script_id}/scenes", response_model=List[SceneResponse])
async def list_scenes_for_script(
    script_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneResponse.model_validate(s)
        for s in svc.list_scenes_by_script(db, script_id)
    ]


@router.get("/scripts/{script_id}/structure", response_model=ScriptStructureResponse)
async def get_script_structure(
    script_id: int,
    db: Session = Depends(get_db),
):
    aggregated = svc.get_script_structure(db, script_id)
    if aggregated is None:
        raise HTTPException(status_code=404, detail="script not found")

    scenes_payload = []
    for item in aggregated:
        scene_dict = SceneResponse.model_validate(item["scene"]).model_dump()
        scene_dict["beats"] = [
            SceneBeatResponse.model_validate(b).model_dump()
            for b in item.get("beats", [])
        ]
        scene_dict["shots"] = [
            ShotResponse.model_validate(sh).model_dump() for sh in item.get("shots", [])
        ]
        scenes_payload.append(SceneWithChildren.model_validate(scene_dict))

    return ScriptStructureResponse(script_id=script_id, scenes=scenes_payload)


@router.post("/scripts/{script_id}/scenes", response_model=SceneResponse)
async def create_scene_for_script(
    script_id: int,
    body: SceneCreate,
    db: Session = Depends(get_db),
):
    if body.script_id != script_id:
        raise HTTPException(status_code=400, detail="script_id mismatch")
    try:
        obj = svc.create_scene(db, body)
    except ValueError as exc:
        if str(exc) == "script_not_found":
            raise HTTPException(status_code=404, detail="script not found")
        if str(exc) == "environment_not_found":
            raise HTTPException(status_code=404, detail="environment not found")
        raise
    return SceneResponse.model_validate(obj)


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    """Get scene by numeric id."""
    scene = svc.get_scene(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(scene)


@router.get("/scenes/business/{scene_business_id}", response_model=SceneResponse)
async def get_scene_by_business_id(
    scene_business_id: str,
    db: Session = Depends(get_db),
):
    """Get scene by business_id."""
    scene = svc.get_scene_by_business_id(db, scene_business_id)
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(scene)


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: int,
    body: SceneUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_scene(db, scene_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        if str(exc) == "environment_not_found":
            raise HTTPException(status_code=404, detail="environment not found")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(obj)


@router.put("/scenes/business/{scene_business_id}", response_model=SceneResponse)
async def update_scene_by_business_id(
    scene_business_id: str,
    body: SceneUpdate,
    db: Session = Depends(get_db),
):
    """Update scene by business_id."""
    scene = svc.get_scene_by_business_id(db, scene_business_id)
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")
    try:
        obj = svc.update_scene(db, scene.id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        if str(exc) == "environment_not_found":
            raise HTTPException(status_code=404, detail="environment not found")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(obj)


@router.delete("/scenes/{scene_id}", status_code=204)
async def delete_scene(
    scene_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ok = svc.delete_scene(db, scene_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="scene not found")
    return None


@router.delete("/scenes/business/{scene_business_id}", status_code=204)
async def delete_scene_by_business_id(
    scene_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete scene by business_id (soft delete)."""
    scene = svc.get_scene_by_business_id(db, scene_business_id)
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")
    ok = svc.delete_scene(db, scene.id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="scene not found")
    return None


@router.post("/scripts/{script_id}/seed-from-json")
async def seed_scenes_from_json(
    script_id: int,
    dry_run: bool = Query(False, description="Do not write inserts when true"),
    db: Session = Depends(get_db),
):
    count = svc.seed_scenes_from_script_json(db, script_id, dry_run=dry_run)
    return {
        "script_id": script_id,
        "prepared": count,
        "inserted": 0 if dry_run else count,
    }
