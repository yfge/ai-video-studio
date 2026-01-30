from __future__ import annotations

from typing import Optional

from app.models.script import Story
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session


def not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def get_story_by_identifier(
    db: Session,
    story_id: Optional[int],
    story_business_id: Optional[str],
    current_user: User,
) -> Story:
    query = not_deleted(db.query(Story), Story)
    if story_business_id:
        query = query.filter(Story.business_id == story_business_id)
    elif story_id:
        query = query.filter(Story.id == story_id)
    else:
        raise HTTPException(status_code=400, detail="story identifier missing")
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    return story
