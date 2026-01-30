"""
Story Structure scene beat endpoints.

Scene beat CRUD operations.
"""

from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.story_structure import (
    SceneBeatCreate,
    SceneBeatResponse,
    SceneBeatUpdate,
)
from app.services import story_structure_service as svc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/scenes/{scene_id}/beats", response_model=List[SceneBeatResponse])
async def list_beats_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneBeatResponse.model_validate(b)
        for b in svc.list_beats_by_scene(db, scene_id)
    ]


@router.post("/scenes/{scene_id}/beats", response_model=SceneBeatResponse)
async def create_beat_for_scene(
    scene_id: int,
    body: SceneBeatCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    try:
        obj = svc.create_scene_beat(db, body)
    except ValueError as exc:
        if str(exc) == "duplicate_order_index":
            raise HTTPException(
                status_code=400,
                detail="order_index already exists for scene",
            )
        raise
    return SceneBeatResponse.model_validate(obj)


@router.get("/scene-beats/{beat_id}", response_model=SceneBeatResponse)
async def get_scene_beat(
    beat_id: int,
    db: Session = Depends(get_db),
):
    """Get scene beat by numeric id."""
    beat = svc.get_scene_beat(db, beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(beat)


@router.get(
    "/scene-beats/business/{beat_business_id}", response_model=SceneBeatResponse
)
async def get_scene_beat_by_business_id(
    beat_business_id: str,
    db: Session = Depends(get_db),
):
    """Get scene beat by business_id."""
    beat = svc.get_scene_beat_by_business_id(db, beat_business_id)
    if not beat:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(beat)


@router.put("/scene-beats/{beat_id}", response_model=SceneBeatResponse)
async def update_scene_beat(
    beat_id: int,
    body: SceneBeatUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_scene_beat(db, beat_id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        if str(exc) == "duplicate_order_index":
            raise HTTPException(
                status_code=400, detail="order_index already exists for scene"
            )
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(obj)


@router.put(
    "/scene-beats/business/{beat_business_id}", response_model=SceneBeatResponse
)
async def update_scene_beat_by_business_id(
    beat_business_id: str,
    body: SceneBeatUpdate,
    db: Session = Depends(get_db),
):
    """Update scene beat by business_id."""
    beat = svc.get_scene_beat_by_business_id(db, beat_business_id)
    if not beat:
        raise HTTPException(status_code=404, detail="beat not found")
    try:
        obj = svc.update_scene_beat(db, beat.id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        if str(exc) == "duplicate_order_index":
            raise HTTPException(
                status_code=400, detail="order_index already exists for scene"
            )
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(obj)


@router.delete("/scene-beats/{beat_id}", status_code=204)
async def delete_scene_beat(
    beat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ok = svc.delete_scene_beat(db, beat_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="beat not found")
    return None


@router.delete("/scene-beats/business/{beat_business_id}", status_code=204)
async def delete_scene_beat_by_business_id(
    beat_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete scene beat by business_id (soft delete)."""
    beat = svc.get_scene_beat_by_business_id(db, beat_business_id)
    if not beat:
        raise HTTPException(status_code=404, detail="beat not found")
    ok = svc.delete_scene_beat(db, beat.id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="beat not found")
    return None
