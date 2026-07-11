from __future__ import annotations

import json
from typing import Literal

from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.production_canvas_collaboration import CanvasAccessRole
from sqlalchemy.orm import Session

CanvasCapability = Literal["view", "comment", "edit", "approve", "execute", "manage"]

_CAPABILITIES: dict[CanvasAccessRole, set[CanvasCapability]] = {
    "owner": {"view", "comment", "edit", "approve", "execute", "manage"},
    "viewer": {"view"},
    "commenter": {"view", "comment"},
    "editor": {"view", "comment", "edit"},
    "approver": {"view", "comment", "approve"},
}


def decode_canvas_run_payload(task: Task) -> dict | None:
    if not task.parameters:
        return None
    try:
        payload = json.loads(task.parameters)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or payload.get("kind") != "production_canvas_run":
        return None
    return payload


def canvas_access_role(
    task: Task, payload: dict, user: User
) -> CanvasAccessRole | None:
    if task.user_id == user.id:
        return "owner"
    for item in payload.get("canvas_collaborators") or []:
        if not isinstance(item, dict) or item.get("user_id") != user.id:
            continue
        role = item.get("role")
        if role in _CAPABILITIES and role != "owner":
            return role
    return None


def canvas_run_access(
    db: Session,
    user: User,
    run_id: str,
    capability: CanvasCapability = "view",
    *,
    for_update: bool = False,
) -> tuple[Task, dict, CanvasAccessRole] | None:
    if not run_id:
        return None
    task = TaskRepository(db).get_canvas_run_task(run_id)
    if task is None:
        return None
    if for_update:
        db.refresh(task, with_for_update=True)
    payload = decode_canvas_run_payload(task)
    if payload is None:
        return None
    role = canvas_access_role(task, payload, user)
    if role is None or capability not in _CAPABILITIES[role]:
        return None
    return task, payload, role


def require_canvas_access(
    db: Session,
    user: User,
    run_id: str,
    capability: CanvasCapability,
) -> CanvasAccessRole:
    access = canvas_run_access(db, user, run_id, capability)
    if access is None:
        raise ValueError("canvas_access_forbidden")
    return access[2]


def require_canvas_access_if_run_exists(
    db: Session,
    user: User,
    run_id: str,
    capability: CanvasCapability,
) -> None:
    task = TaskRepository(db).get_canvas_run_task(run_id)
    if task is None or decode_canvas_run_payload(task) is None:
        return
    require_canvas_access(db, user, run_id, capability)


def canvas_run_owner(db: Session, user: User, run_id: str) -> User:
    access = canvas_run_access(db, user, run_id, "view")
    if access is None:
        raise ValueError("canvas_access_forbidden")
    owner = UserRepository(db).get_by_id(access[0].user_id)
    if owner is None:
        raise ValueError("canvas_run_owner_not_found")
    return owner
