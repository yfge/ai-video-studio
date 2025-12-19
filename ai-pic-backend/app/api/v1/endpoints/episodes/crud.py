"""
Episode CRUD endpoints.

Basic create, read, update, delete operations for episodes.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode
from app.models.user import User
from app.schemas.script import (
    EpisodeCreate,
    EpisodeUpdate,
    EpisodeResponse,
)
from .helpers import (
    not_deleted,
    get_episode_by_identifier,
    get_story_by_identifier,
)

router = APIRouter()


@router.post("/", response_model=EpisodeResponse)
async def create_episode(
    episode: EpisodeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new episode."""
    # Check if story exists
    story_query = not_deleted(db.query(Story), Story).filter(
        Story.id == episode.story_id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # Check for duplicate episode number
    existing_episode = (
        not_deleted(db.query(Episode), Episode)
        .filter(
            Episode.story_id == episode.story_id,
            Episode.episode_number == episode.episode_number,
        )
        .first()
    )
    if existing_episode:
        raise HTTPException(status_code=400, detail="该集数已存在")

    db_episode = Episode(**episode.dict())
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)

    return EpisodeResponse.from_orm(db_episode)


@router.get("/", response_model=List[EpisodeResponse])
async def get_episodes(
    story_id: Optional[int] = Query(None),
    story_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get list of episodes with optional filtering."""
    query = (
        not_deleted(db.query(Episode), Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Story.is_deleted.is_(False))
    )

    # Regular users can only view their own episodes
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)

    if story_id:
        query = query.filter(Episode.story_id == story_id)
    if story_business_id:
        query = query.filter(Story.business_id == story_business_id)

    if status:
        query = query.filter(Episode.status == status)

    episodes = (
        query.order_by(Episode.story_id, Episode.episode_number)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [EpisodeResponse.from_orm(episode) for episode in episodes]


@router.get("", response_model=List[EpisodeResponse], include_in_schema=False)
async def get_episodes_no_slash(
    story_id: Optional[int] = Query(None),
    story_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Compatibility endpoint for requests without trailing slash."""
    return await get_episodes(
        story_id=story_id,
        story_business_id=story_business_id,
        skip=skip,
        limit=limit,
        status=status,
        current_user=current_user,
        db=db,
    )


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get episode details by ID."""
    episode = get_episode_by_identifier(db, episode_id, None, current_user)
    return EpisodeResponse.from_orm(episode)


@router.get("/business/{episode_business_id}", response_model=EpisodeResponse)
async def get_episode_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get episode details by business ID."""
    episode = get_episode_by_identifier(db, None, episode_business_id, current_user)
    return EpisodeResponse.from_orm(episode)


@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    episode_update: EpisodeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update an episode by ID."""
    episode = get_episode_by_identifier(db, episode_id, None, current_user)

    # Check for duplicate episode number if updating
    if (
        episode_update.episode_number
        and episode_update.episode_number != episode.episode_number
    ):
        existing_episode = (
            db.query(Episode)
            .filter(
                Episode.story_id == episode.story_id,
                Episode.episode_number == episode_update.episode_number,
                Episode.id != episode_id,
            )
            .first()
        )
        if existing_episode:
            raise HTTPException(status_code=400, detail="该集数已存在")

    # Update episode fields
    for field, value in episode_update.dict(exclude_unset=True).items():
        setattr(episode, field, value)

    db.commit()
    db.refresh(episode)

    return EpisodeResponse.from_orm(episode)


@router.put("/business/{episode_business_id}", response_model=EpisodeResponse)
async def update_episode_by_business_id(
    episode_business_id: str,
    episode_update: EpisodeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update an episode by business ID."""
    episode = get_episode_by_identifier(db, None, episode_business_id, current_user)

    if (
        episode_update.episode_number
        and episode_update.episode_number != episode.episode_number
    ):
        existing_episode = (
            db.query(Episode)
            .filter(
                Episode.story_id == episode.story_id,
                Episode.episode_number == episode_update.episode_number,
                Episode.id != episode.id,
                Episode.is_deleted.is_(False),
            )
            .first()
        )
        if existing_episode:
            raise HTTPException(status_code=400, detail="该集数已存在")

    for field, value in episode_update.dict(exclude_unset=True).items():
        setattr(episode, field, value)

    db.commit()
    db.refresh(episode)

    return EpisodeResponse.from_orm(episode)


@router.delete("/{episode_id}")
async def delete_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an episode by ID (soft delete)."""
    episode = get_episode_by_identifier(db, episode_id, None, current_user)
    episode.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "剧集删除成功"}


@router.delete("/business/{episode_business_id}")
async def delete_episode_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an episode by business ID (soft delete)."""
    episode = get_episode_by_identifier(db, None, episode_business_id, current_user)
    episode.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "剧集删除成功"}


@router.get("/story/{story_id}")
async def get_story_episodes(
    story_id: int,
    story_business_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all episodes for a story by story ID."""
    story = get_story_by_identifier(db, story_id, story_business_id, current_user)

    episodes = (
        not_deleted(db.query(Episode), Episode)
        .filter(Episode.story_id == story.id)
        .order_by(Episode.episode_number)
        .all()
    )
    return {
        "success": True,
        "data": (
            [EpisodeResponse.from_orm(episode) for episode in episodes]
            if episodes
            else []
        ),
    }


@router.get("/story/business/{story_business_id}")
async def get_story_episodes_by_business_id(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all episodes for a story by story business ID."""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    episodes = (
        not_deleted(db.query(Episode), Episode)
        .filter(Episode.story_id == story.id)
        .order_by(Episode.episode_number)
        .all()
    )
    return {
        "success": True,
        "data": (
            [EpisodeResponse.from_orm(episode) for episode in episodes]
            if episodes
            else []
        ),
    }
