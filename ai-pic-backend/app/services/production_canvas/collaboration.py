from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.production_canvas_collaboration import (
    ProductionCanvasActivity,
    ProductionCanvasCollaborationResponse,
    ProductionCanvasCollaborator,
    ProductionCanvasCollaboratorRequest,
    ProductionCanvasComment,
    ProductionCanvasCommentRequest,
)
from sqlalchemy.orm import Session

from .access_control import canvas_run_access


def _items(payload: dict, key: str, schema):
    values = []
    for item in payload.get(key) or []:
        if not isinstance(item, dict):
            continue
        try:
            values.append(schema.model_validate(item))
        except ValueError:
            continue
    return values


def _activity(
    user: User,
    action: str,
    *,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
) -> ProductionCanvasActivity:
    return ProductionCanvasActivity(
        activity_id=uuid4().hex,
        action=action,
        actor_id=user.id,
        actor_username=user.username,
        target_type=target_type,
        target_id=target_id,
        detail=detail[:500] if detail else None,
        created_at=datetime.now(UTC),
    )


def _append_activity(payload: dict, item: ProductionCanvasActivity) -> None:
    history = list(payload.get("canvas_activity") or [])
    history.append(item.model_dump(mode="json"))
    payload["canvas_activity"] = history[-500:]


def append_canvas_activity(
    payload: dict,
    user: User,
    action: str,
    *,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
) -> None:
    _append_activity(
        payload,
        _activity(
            user,
            action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        ),
    )


def load_canvas_collaboration(
    db: Session, user: User, run_id: str
) -> ProductionCanvasCollaborationResponse:
    access = canvas_run_access(db, user, run_id, "view")
    if access is None:
        raise ValueError("canvas_access_forbidden")
    _, payload, role = access
    return ProductionCanvasCollaborationResponse(
        access_role=role,
        collaborators=_items(
            payload, "canvas_collaborators", ProductionCanvasCollaborator
        ),
        comments=_items(payload, "canvas_comments", ProductionCanvasComment),
        activity=_items(payload, "canvas_activity", ProductionCanvasActivity),
    )


def upsert_canvas_collaborator(
    db: Session,
    user: User,
    run_id: str,
    request: ProductionCanvasCollaboratorRequest,
) -> ProductionCanvasCollaborationResponse:
    access = canvas_run_access(db, user, run_id, "manage", for_update=True)
    if access is None:
        raise ValueError("canvas_access_forbidden")
    task, payload, _ = access
    collaborator = UserRepository(db).get_by(
        username=request.username, is_deleted=False
    )
    if collaborator is None:
        raise ValueError("canvas_collaborator_not_found")
    if collaborator.id == task.user_id:
        raise ValueError("canvas_owner_role_immutable")
    item = ProductionCanvasCollaborator(
        user_id=collaborator.id,
        username=collaborator.username,
        role=request.role,
        added_by=user.id,
        added_at=datetime.now(UTC),
    )
    existing = _items(payload, "canvas_collaborators", ProductionCanvasCollaborator)
    payload["canvas_collaborators"] = [
        *(
            entry.model_dump(mode="json")
            for entry in existing
            if entry.user_id != item.user_id
        ),
        item.model_dump(mode="json"),
    ]
    _append_activity(
        payload,
        _activity(
            user,
            "collaborator.updated",
            target_type="user",
            target_id=str(item.user_id),
            detail=f"{item.username}: {item.role}",
        ),
    )
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return load_canvas_collaboration(db, user, run_id)


def remove_canvas_collaborator(
    db: Session, user: User, run_id: str, collaborator_id: int
) -> ProductionCanvasCollaborationResponse:
    access = canvas_run_access(db, user, run_id, "manage", for_update=True)
    if access is None:
        raise ValueError("canvas_access_forbidden")
    task, payload, _ = access
    existing = _items(payload, "canvas_collaborators", ProductionCanvasCollaborator)
    if not any(item.user_id == collaborator_id for item in existing):
        raise ValueError("canvas_collaborator_not_found")
    payload["canvas_collaborators"] = [
        item.model_dump(mode="json")
        for item in existing
        if item.user_id != collaborator_id
    ]
    _append_activity(
        payload,
        _activity(
            user,
            "collaborator.removed",
            target_type="user",
            target_id=str(collaborator_id),
        ),
    )
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return load_canvas_collaboration(db, user, run_id)


def add_canvas_comment(
    db: Session,
    user: User,
    run_id: str,
    request: ProductionCanvasCommentRequest,
) -> ProductionCanvasCollaborationResponse:
    access = canvas_run_access(db, user, run_id, "comment", for_update=True)
    if access is None:
        raise ValueError("canvas_access_forbidden")
    task, payload, _ = access
    item = ProductionCanvasComment(
        comment_id=uuid4().hex,
        target_type=request.target_type,
        target_id=request.target_id,
        body=request.body,
        author_id=user.id,
        author_username=user.username,
        created_at=datetime.now(UTC),
    )
    comments = list(payload.get("canvas_comments") or [])
    comments.append(item.model_dump(mode="json"))
    payload["canvas_comments"] = comments[-1000:]
    _append_activity(
        payload,
        _activity(
            user,
            "comment.added",
            target_type=request.target_type,
            target_id=request.target_id,
            detail=item.body[:500],
        ),
    )
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return load_canvas_collaboration(db, user, run_id)


def record_canvas_activity(
    db: Session,
    user: User,
    run_id: str,
    action: str,
    *,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
) -> None:
    access = canvas_run_access(db, user, run_id, "view", for_update=True)
    if access is None:
        return
    task, payload, _ = access
    append_canvas_activity(
        payload,
        user,
        action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
