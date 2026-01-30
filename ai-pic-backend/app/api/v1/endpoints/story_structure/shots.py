"""
Story Structure shot endpoints.

Shot CRUD operations.
"""

from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.story_structure import ShotCreate, ShotResponse, ShotUpdate
from app.services import story_structure_service as svc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/scenes/{scene_id}/shots", response_model=List[ShotResponse])
async def list_shots_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        ShotResponse.model_validate(sh) for sh in svc.list_shots_by_scene(db, scene_id)
    ]


@router.post("/scenes/{scene_id}/shots", response_model=ShotResponse)
async def create_shot_for_scene(
    scene_id: int,
    body: ShotCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    try:
        obj = svc.create_shot(db, body)
    except ValueError as exc:
        msg = str(exc)
        if msg == "scene_not_found":
            raise HTTPException(status_code=404, detail="scene not found")
        if msg == "duplicate_shot_number":
            raise HTTPException(
                status_code=400, detail="shot_number already exists for scene"
            )
        if msg == "beat_scene_mismatch":
            raise HTTPException(status_code=400, detail="beat does not belong to scene")
        raise
    return ShotResponse.model_validate(obj)


@router.get("/shots/{shot_id}", response_model=ShotResponse)
async def get_shot(
    shot_id: int,
    db: Session = Depends(get_db),
):
    """Get shot by numeric id."""
    shot = svc.get_shot(db, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(shot)


@router.get("/shots/business/{shot_business_id}", response_model=ShotResponse)
async def get_shot_by_business_id(
    shot_business_id: str,
    db: Session = Depends(get_db),
):
    """Get shot by business_id."""
    shot = svc.get_shot_by_business_id(db, shot_business_id)
    if not shot:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(shot)


@router.put("/shots/{shot_id}", response_model=ShotResponse)
async def update_shot(
    shot_id: int,
    body: ShotUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_shot(db, shot_id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        msg = str(exc)
        if msg == "duplicate_shot_number":
            raise HTTPException(
                status_code=400, detail="shot_number already exists for scene"
            )
        if msg == "beat_scene_mismatch":
            raise HTTPException(status_code=400, detail="beat does not belong to scene")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(obj)


@router.put("/shots/business/{shot_business_id}", response_model=ShotResponse)
async def update_shot_by_business_id(
    shot_business_id: str,
    body: ShotUpdate,
    db: Session = Depends(get_db),
):
    """Update shot by business_id."""
    shot = svc.get_shot_by_business_id(db, shot_business_id)
    if not shot:
        raise HTTPException(status_code=404, detail="shot not found")
    try:
        obj = svc.update_shot(db, shot.id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        msg = str(exc)
        if msg == "duplicate_shot_number":
            raise HTTPException(
                status_code=400, detail="shot_number already exists for scene"
            )
        if msg == "beat_scene_mismatch":
            raise HTTPException(status_code=400, detail="beat does not belong to scene")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(obj)


@router.delete("/shots/{shot_id}", status_code=204)
async def delete_shot(
    shot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ok = svc.delete_shot(db, shot_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="shot not found")
    return None


@router.delete("/shots/business/{shot_business_id}", status_code=204)
async def delete_shot_by_business_id(
    shot_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete shot by business_id (soft delete)."""
    shot = svc.get_shot_by_business_id(db, shot_business_id)
    if not shot:
        raise HTTPException(status_code=404, detail="shot not found")
    ok = svc.delete_shot(db, shot.id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="shot not found")
    return None
