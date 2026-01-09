from __future__ import annotations

from typing import Any, Dict

from app.models.user import User
from app.services import story_structure_service as svc
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


async def read_json_payload(request: Request) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
    return payload


def get_owned_environment_or_404(db: Session, env_id: str, current_user: User):
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return env
