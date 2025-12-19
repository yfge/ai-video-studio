"""
Story Structure shot endpoints.

Shot CRUD operations.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.story_structure import (
    ShotCreate,
    ShotResponse,
    ShotUpdate,
)
from app.services import story_structure_service as svc

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


@router.delete("/shots/{shot_id}", status_code=204)
async def delete_shot(shot_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_shot(db, shot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="shot not found")
    return None
