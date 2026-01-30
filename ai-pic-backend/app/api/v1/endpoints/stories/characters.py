from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import StoryCharacter
from app.models.user import User
from app.schemas.script import StoryCharacterResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .helpers import get_story_by_identifier, not_deleted

router = APIRouter()


@router.get("/{story_id}/characters", response_model=List[StoryCharacterResponse])
async def get_story_characters(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事角色列表"""
    story = get_story_by_identifier(db, story_id, None, current_user)

    characters = (
        not_deleted(db.query(StoryCharacter), StoryCharacter)
        .filter(StoryCharacter.story_id == story.id)
        .all()
    )
    return [StoryCharacterResponse.from_orm(char) for char in characters]


@router.get(
    "/business/{story_business_id}/characters",
    response_model=List[StoryCharacterResponse],
)
async def get_story_characters_by_business_id(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 获取故事角色列表"""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    characters = (
        not_deleted(db.query(StoryCharacter), StoryCharacter)
        .filter(StoryCharacter.story_id == story.id)
        .all()
    )
    return [StoryCharacterResponse.from_orm(char) for char in characters]
