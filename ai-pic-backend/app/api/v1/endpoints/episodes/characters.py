"""
Episode Character endpoints.

Manages temporary characters for episodes - binding VirtualIPs to episodes
for temporary roles like delivery person, passerby, doctor, etc.
"""

from typing import Union

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.episode_character import EpisodeCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.episode_character import (
    EpisodeCharacterCreate,
    EpisodeCharacterListResponse,
    EpisodeCharacterResponse,
    EpisodeCharacterUpdate,
    EpisodeCharacterWithResources,
)
from app.services.episode_character_service import (
    get_episode_characters,
    resolve_character_resources,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .helpers import get_episode_by_identifier

router = APIRouter()


@router.post("/{episode_id}/characters", response_model=EpisodeCharacterResponse)
async def create_episode_character(
    episode_id: Union[int, str],
    data: EpisodeCharacterCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a temporary character for an episode.

    Requires:
    - virtual_ip_id: Must exist and be accessible by current user
    - Episode must exist and be accessible by current user
    """
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Verify VirtualIP exists
    virtual_ip_query = db.query(VirtualIP).filter(
        VirtualIP.id == data.virtual_ip_id,
        VirtualIP.is_deleted == False,
    )

    # Non-admin users can only use their own VirtualIPs
    if not current_user.is_admin and not current_user.is_superuser:
        virtual_ip_query = virtual_ip_query.filter(VirtualIP.user_id == current_user.id)

    virtual_ip = virtual_ip_query.first()
    if not virtual_ip:
        raise HTTPException(
            status_code=404,
            detail="VirtualIP not found or you don't have permission to use it",
        )

    # Create episode character
    character = EpisodeCharacter(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        **data.model_dump(exclude={"virtual_ip_id"}),
    )

    db.add(character)
    db.commit()
    db.refresh(character)

    return character


@router.get("/{episode_id}/characters", response_model=EpisodeCharacterListResponse)
async def list_episode_characters(
    episode_id: Union[int, str],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_deleted: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List temporary characters for an episode (paginated).

    Returns characters sorted by importance (descending) and creation time.
    """
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    result = get_episode_characters(
        db=db,
        episode_id=episode.id,
        page=page,
        page_size=page_size,
        include_deleted=include_deleted,
    )

    return result


@router.get(
    "/{episode_id}/characters/{character_id}",
    response_model=EpisodeCharacterResponse,
)
async def get_episode_character(
    episode_id: Union[int, str],
    character_id: Union[int, str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific episode character."""
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Query character
    query = db.query(EpisodeCharacter).filter(EpisodeCharacter.episode_id == episode.id)

    # Support both ID and business_id lookup
    if isinstance(character_id, str) and not character_id.isdigit():
        query = query.filter(EpisodeCharacter.business_id == character_id)
    else:
        query = query.filter(EpisodeCharacter.id == int(character_id))

    character = query.first()
    if not character or character.is_deleted:
        raise HTTPException(status_code=404, detail="Episode character not found")

    return character


@router.get(
    "/{episode_id}/characters/{character_id}/resources",
    response_model=EpisodeCharacterWithResources,
)
async def get_episode_character_resources(
    episode_id: Union[int, str],
    character_id: Union[int, str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get episode character with resolved resources.

    Returns character with:
    - resolved_voice_config: voice_config_override or VirtualIP.voice_config
    - resolved_images: VirtualIP images sorted by priority
    - resolved_appearance_prompt: merged appearance description
    - display_name: character_name or VirtualIP.name
    """
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Query character with VirtualIP
    query = (
        db.query(EpisodeCharacter)
        .options(joinedload(EpisodeCharacter.virtual_ip).joinedload(VirtualIP.images))
        .filter(EpisodeCharacter.episode_id == episode.id)
    )

    # Support both ID and business_id lookup
    if isinstance(character_id, str) and not character_id.isdigit():
        query = query.filter(EpisodeCharacter.business_id == character_id)
    else:
        query = query.filter(EpisodeCharacter.id == int(character_id))

    character = query.first()
    if not character or character.is_deleted:
        raise HTTPException(status_code=404, detail="Episode character not found")

    # Resolve resources
    resources = resolve_character_resources(character, db)

    # Build response
    response_data = EpisodeCharacterResponse.model_validate(character).model_dump()
    response_data.update(
        {
            "resolved_voice_config": resources["voice_config"],
            "resolved_images": resources["images"],
            "resolved_appearance_prompt": resources["appearance_prompt"],
            "display_name": resources["display_name"],
        }
    )

    return response_data


@router.put(
    "/{episode_id}/characters/{character_id}",
    response_model=EpisodeCharacterResponse,
)
async def update_episode_character(
    episode_id: Union[int, str],
    character_id: Union[int, str],
    data: EpisodeCharacterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update an episode character.

    Note: virtual_ip_id cannot be changed after creation.
    """
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Query character
    query = db.query(EpisodeCharacter).filter(EpisodeCharacter.episode_id == episode.id)

    # Support both ID and business_id lookup
    if isinstance(character_id, str) and not character_id.isdigit():
        query = query.filter(EpisodeCharacter.business_id == character_id)
    else:
        query = query.filter(EpisodeCharacter.id == int(character_id))

    character = query.first()
    if not character or character.is_deleted:
        raise HTTPException(status_code=404, detail="Episode character not found")

    # Update fields (exclude None values)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    db.commit()
    db.refresh(character)

    return character


@router.delete("/{episode_id}/characters/{character_id}")
async def delete_episode_character(
    episode_id: Union[int, str],
    character_id: Union[int, str],
    reason: str = Query(None, description="Deletion reason"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Soft delete an episode character.

    The character is marked as deleted but not removed from the database.
    """
    # Verify episode access
    episode = get_episode_by_identifier(db, episode_id, current_user)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Query character
    query = db.query(EpisodeCharacter).filter(EpisodeCharacter.episode_id == episode.id)

    # Support both ID and business_id lookup
    if isinstance(character_id, str) and not character_id.isdigit():
        query = query.filter(EpisodeCharacter.business_id == character_id)
    else:
        query = query.filter(EpisodeCharacter.id == int(character_id))

    character = query.first()
    if not character or character.is_deleted:
        raise HTTPException(status_code=404, detail="Episode character not found")

    # Soft delete
    character.soft_delete(user_id=current_user.id, reason=reason)
    db.commit()

    return {"message": "Episode character deleted successfully"}
