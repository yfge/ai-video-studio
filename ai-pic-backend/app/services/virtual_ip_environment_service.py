from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.virtual_ip_environment_repository import (
    VirtualIPEnvironmentRepository,
)
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.virtual_ip_environment import (
    VirtualIPEnvironmentCreate,
    VirtualIPEnvironmentUpdate,
    VirtualIPLinkSummary,
)
from sqlalchemy.orm import Session


def _resolve_virtual_ip(db: Session, user: User, ip_id: int | str) -> VirtualIP:
    repo = VirtualIPRepository(db)
    raw = str(ip_id)
    if raw.isdigit():
        return repo.get_owned_by_id(int(raw), user)
    return repo.get_owned_by_business_id(raw, user)


def list_virtual_ip_environments(
    db: Session,
    user: User,
    *,
    ip_id: int | str,
) -> list[VirtualIPEnvironment]:
    virtual_ip = _resolve_virtual_ip(db, user, ip_id)
    return VirtualIPEnvironmentRepository(db).list_for_virtual_ip(virtual_ip.id)


def link_environment_to_virtual_ip(
    db: Session,
    user: User,
    *,
    ip_id: int | str,
    payload: VirtualIPEnvironmentCreate,
) -> VirtualIPEnvironment:
    virtual_ip = _resolve_virtual_ip(db, user, ip_id)
    environment = EnvironmentRepository(db).get_owned_by_identifier(
        payload.environment_id, user
    )
    repo = VirtualIPEnvironmentRepository(db)
    existing = repo.get_pair(
        virtual_ip_id=virtual_ip.id,
        environment_id=environment.id,
        include_deleted=True,
    )
    data = payload.model_dump(exclude={"environment_id"})
    if existing:
        for field, value in data.items():
            setattr(existing, field, value)
        existing.is_deleted = False
        existing.deleted_at = None
        existing.deleted_by = None
        existing.deleted_reason = None
        existing.user_id = user.id
        existing.virtual_ip_business_id = virtual_ip.business_id
        existing.environment_business_id = environment.business_id
        link = existing
    else:
        link = VirtualIPEnvironment(
            user_id=user.id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            environment_id=environment.id,
            environment_business_id=environment.business_id,
            **data,
        )
        db.add(link)

    db.commit()
    db.refresh(link)
    return link


def update_virtual_ip_environment_link(
    db: Session,
    user: User,
    *,
    ip_id: int | str,
    environment_id: int | str,
    payload: VirtualIPEnvironmentUpdate,
) -> VirtualIPEnvironment:
    virtual_ip = _resolve_virtual_ip(db, user, ip_id)
    environment = EnvironmentRepository(db).get_owned_by_identifier(
        environment_id, user
    )
    repo = VirtualIPEnvironmentRepository(db)
    link = repo.get_pair(
        virtual_ip_id=virtual_ip.id,
        environment_id=environment.id,
    )
    if not link:
        raise NotFoundError("IP环境关联", environment_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, field, value)
    db.commit()
    db.refresh(link)
    return link


def unlink_environment_from_virtual_ip(
    db: Session,
    user: User,
    *,
    ip_id: int | str,
    environment_id: int | str,
) -> bool:
    virtual_ip = _resolve_virtual_ip(db, user, ip_id)
    environment = EnvironmentRepository(db).get_owned_by_identifier(
        environment_id, user
    )
    link = VirtualIPEnvironmentRepository(db).get_pair(
        virtual_ip_id=virtual_ip.id,
        environment_id=environment.id,
    )
    if not link:
        return False
    link.soft_delete(user_id=user.id, reason="virtual_ip_environment_unlinked")
    db.commit()
    return True


def list_environment_link_summaries(
    db: Session,
    user: User,
    *,
    environment_ids: list[int],
) -> dict[int, list[VirtualIPLinkSummary]]:
    links = VirtualIPEnvironmentRepository(db).list_for_environment_ids(
        environment_ids, user
    )
    grouped: dict[int, list[VirtualIPLinkSummary]] = {}
    for link in links:
        vip = link.virtual_ip
        if not vip:
            continue
        grouped.setdefault(link.environment_id, []).append(
            VirtualIPLinkSummary.model_validate(vip)
        )
    return grouped
