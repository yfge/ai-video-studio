"""
Story Structure treatment endpoints.

Story treatment and step outline CRUD operations.
"""

from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.schemas.story_structure import (
    StoryStepOutlineCreate,
    StoryStepOutlineResponse,
    StoryTreatmentCreate,
    StoryTreatmentResponse,
)
from app.services import story_structure_service as svc
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/stories/{story_id}/treatments", response_model=List[StoryTreatmentResponse]
)
async def list_treatments(
    story_id: int,
    latest_only: bool = Query(False, description="仅返回最新一条修订"),
    db: Session = Depends(get_db),
):
    items = svc.list_treatments_by_story(db, story_id)
    if latest_only:
        return [StoryTreatmentResponse.model_validate(items[0])] if items else []
    return [StoryTreatmentResponse.model_validate(it) for it in items]


@router.post("/stories/{story_id}/treatments", response_model=StoryTreatmentResponse)
async def create_treatment(
    story_id: int,
    body: StoryTreatmentCreate,
    db: Session = Depends(get_db),
):
    if body.story_id != story_id:
        raise HTTPException(status_code=400, detail="story_id mismatch")
    obj = svc.create_treatment(db, body)
    return StoryTreatmentResponse.model_validate(obj)


@router.get(
    "/treatments/{treatment_id}/step-outlines",
    response_model=List[StoryStepOutlineResponse],
)
async def list_step_outlines_for_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
):
    outlines = svc.list_step_outlines(db, treatment_id)
    return [StoryStepOutlineResponse.model_validate(it) for it in outlines]


@router.post(
    "/treatments/{treatment_id}/step-outlines", response_model=StoryStepOutlineResponse
)
async def create_step_outline_for_treatment(
    treatment_id: int,
    body: StoryStepOutlineCreate,
    db: Session = Depends(get_db),
):
    if body.story_treatment_id != treatment_id:
        raise HTTPException(status_code=400, detail="story_treatment_id mismatch")
    treatment = svc.get_treatment(db, treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="treatment not found")
    if body.story_id != treatment.story_id:
        raise HTTPException(status_code=400, detail="story_id does not match treatment")
    obj = svc.create_step_outline(db, body)
    return StoryStepOutlineResponse.model_validate(obj)
