from typing import Any, Dict, List, Optional

from app.models.episode_character import EpisodeCharacter
from app.models.virtual_ip import VirtualIP
from sqlalchemy.orm import Session


def resolve_character_resources(
    character: EpisodeCharacter, db: Session
) -> Dict[str, Any]:
    """
    Resolve character resources from VirtualIP with override support.

    Returns:
        - voice_config: override or VirtualIP default
        - images: VirtualIP.images list (sorted by priority)
        - appearance_prompt: merged appearance description
        - display_name: character_name or VirtualIP.name
    """
    # Load VirtualIP if not already loaded
    virtual_ip = character.virtual_ip
    if not virtual_ip:
        virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == character.virtual_ip_id).first()

    if not virtual_ip:
        return {
            "voice_config": None,
            "images": [],
            "appearance_prompt": None,
            "display_name": character.character_name or f"临时角色{character.id}",
        }

    # Voice config: use override if present, else VirtualIP default
    voice_config = character.voice_config_override or virtual_ip.voice_config

    # Images: use VirtualIP images, sorted by is_default and created_at
    images = []
    if virtual_ip.images:
        sorted_images = sorted(
            [img for img in virtual_ip.images if not img.is_deleted],
            key=lambda x: (not x.is_default, x.created_at),
        )
        images = [
            {
                "id": img.id,
                "business_id": img.business_id,
                "filename": img.filename,
                "oss_url": img.oss_url,
                "category": img.category,
                "subcategory": img.subcategory,
                "is_default": img.is_default,
                "tags": img.tags,
            }
            for img in sorted_images
        ]

    # Appearance: merge VirtualIP.style_prompt + appearance_override
    appearance_parts = []
    if virtual_ip.style_prompt:
        appearance_parts.append(virtual_ip.style_prompt)
    if character.appearance_override:
        appearance_parts.append(character.appearance_override)
    appearance_prompt = " ".join(appearance_parts) if appearance_parts else None

    # Display name: priority order
    display_name = (
        character.character_name
        or virtual_ip.name
        or f"临时角色{character.id}"
    )

    return {
        "voice_config": voice_config,
        "images": images,
        "appearance_prompt": appearance_prompt,
        "display_name": display_name,
    }


def get_character_display_name(character: EpisodeCharacter, db: Session) -> str:
    """
    Get display name for character.

    Priority: character_name > VirtualIP.name > "临时角色{id}"
    """
    if character.character_name:
        return character.character_name

    virtual_ip = character.virtual_ip
    if not virtual_ip:
        virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == character.virtual_ip_id).first()

    if virtual_ip and virtual_ip.name:
        return virtual_ip.name

    return f"临时角色{character.id}"


def get_episode_characters(
    db: Session,
    episode_id: int,
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
) -> Dict[str, Any]:
    """
    Get paginated list of Episode characters.

    Returns:
        - items: list of EpisodeCharacter objects
        - total: total count
        - page: current page
        - page_size: items per page
        - has_more: whether more pages exist
    """
    query = db.query(EpisodeCharacter).filter(EpisodeCharacter.episode_id == episode_id)

    if not include_deleted:
        query = query.filter(EpisodeCharacter.is_deleted == False)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(EpisodeCharacter.importance.desc(), EpisodeCharacter.created_at).offset(offset).limit(page_size).all()

    has_more = (offset + len(items)) < total

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": has_more,
    }
