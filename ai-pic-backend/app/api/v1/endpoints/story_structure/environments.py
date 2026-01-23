"""
Story Structure environment endpoints.

Environment CRUD operations.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.story_structure import (
    EnvironmentCreate,
    EnvironmentResponse,
    EnvironmentSummaryResponse,
    EnvironmentUpdate,
)
from app.services import story_structure_service as svc

router = APIRouter()


@router.get("/environments", response_model=List[EnvironmentSummaryResponse])
async def list_environments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items = svc.list_environments(
        db,
        owner_id=(
            None
            if current_user.is_admin or current_user.is_superuser
            else current_user.id
        ),
    )
    return [EnvironmentSummaryResponse.model_validate(it) for it in items]


@router.get("/environments/{env_id}", response_model=EnvironmentResponse)
async def get_environment(
    env_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return EnvironmentResponse.model_validate(env)


@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(
    body: EnvironmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = body.model_dump(exclude_none=True)
    payload["user_id"] = current_user.id
    env = svc.create_environment(db, payload)
    return EnvironmentResponse.model_validate(env)


@router.put("/environments/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: str,
    body: EnvironmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if not env or not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        raise HTTPException(status_code=404, detail="environment not found")
    env = svc.update_environment(db, env_id, body.model_dump(exclude_none=True))
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return EnvironmentResponse.model_validate(env)


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(
    env_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if not env or not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        ok = False
    else:
        ok = svc.delete_environment(db, env_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="environment not found")
    return None
