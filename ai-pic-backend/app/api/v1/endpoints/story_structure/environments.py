"""
Story Structure environment endpoints.

Environment CRUD operations.
"""

from __future__ import annotations

from typing import List

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
from app.services import virtual_ip_environment_service as ip_env_svc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


def _with_linked_virtual_ips(
    dto: EnvironmentResponse | EnvironmentSummaryResponse,
    linked,
):
    payload = dto.model_dump()
    payload["linked_virtual_ips"] = [item.model_dump() for item in linked]
    payload["linked_virtual_ip_count"] = len(linked)
    return payload


def _environment_response_with_links(
    db: Session,
    current_user: User,
    env,
) -> EnvironmentResponse:
    links_by_env = ip_env_svc.list_environment_link_summaries(
        db, current_user, environment_ids=[int(env.id)]
    )
    return EnvironmentResponse.model_validate(
        _with_linked_virtual_ips(
            EnvironmentResponse.model_validate(env),
            links_by_env.get(int(env.id), []),
        )
    )


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
    links_by_env = ip_env_svc.list_environment_link_summaries(
        db, current_user, environment_ids=[int(item.id) for item in items]
    )
    return [
        EnvironmentSummaryResponse.model_validate(
            _with_linked_virtual_ips(
                EnvironmentSummaryResponse.model_validate(item),
                links_by_env.get(int(item.id), []),
            )
        )
        for item in items
    ]


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
    return _environment_response_with_links(db, current_user, env)


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
    return _environment_response_with_links(db, current_user, env)


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
