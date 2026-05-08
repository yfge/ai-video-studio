from __future__ import annotations

from app.core.database import get_db
from app.core.exceptions import DomainError
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.virtual_ip_environment import (
    VirtualIPEnvironmentCreate,
    VirtualIPEnvironmentResponse,
    VirtualIPEnvironmentUpdate,
)
from app.services import virtual_ip_environment_service as svc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


def _raise_http(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{ip_id}/environments", response_model=list[VirtualIPEnvironmentResponse])
@router.get(
    "/business/{ip_business_id}/environments",
    response_model=list[VirtualIPEnvironmentResponse],
)
async def list_virtual_ip_environments(
    ip_id: str | None = None,
    ip_business_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.list_virtual_ip_environments(
            db,
            current_user,
            ip_id=ip_business_id or ip_id or "",
        )
    except DomainError as exc:
        _raise_http(exc)


@router.post("/{ip_id}/environments", response_model=VirtualIPEnvironmentResponse)
@router.post(
    "/business/{ip_business_id}/environments",
    response_model=VirtualIPEnvironmentResponse,
)
async def link_virtual_ip_environment(
    payload: VirtualIPEnvironmentCreate,
    ip_id: str | None = None,
    ip_business_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.link_environment_to_virtual_ip(
            db,
            current_user,
            ip_id=ip_business_id or ip_id or "",
            payload=payload,
        )
    except DomainError as exc:
        _raise_http(exc)


@router.put(
    "/{ip_id}/environments/{environment_id}",
    response_model=VirtualIPEnvironmentResponse,
)
@router.put(
    "/business/{ip_business_id}/environments/{environment_id}",
    response_model=VirtualIPEnvironmentResponse,
)
async def update_virtual_ip_environment(
    environment_id: str,
    payload: VirtualIPEnvironmentUpdate,
    ip_id: str | None = None,
    ip_business_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.update_virtual_ip_environment_link(
            db,
            current_user,
            ip_id=ip_business_id or ip_id or "",
            environment_id=environment_id,
            payload=payload,
        )
    except DomainError as exc:
        _raise_http(exc)


@router.delete("/{ip_id}/environments/{environment_id}", status_code=204)
@router.delete(
    "/business/{ip_business_id}/environments/{environment_id}",
    status_code=204,
)
async def unlink_virtual_ip_environment(
    environment_id: str,
    ip_id: str | None = None,
    ip_business_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        ok = svc.unlink_environment_from_virtual_ip(
            db,
            current_user,
            ip_id=ip_business_id or ip_id or "",
            environment_id=environment_id,
        )
    except DomainError as exc:
        _raise_http(exc)
    if not ok:
        raise HTTPException(status_code=404, detail="IP environment link not found")
    return None
