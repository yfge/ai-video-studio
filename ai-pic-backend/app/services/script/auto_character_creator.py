"""Auto Character Creator Service.

Automatically creates Episode temporary characters from script unknown_names.
Orchestrates extraction, AI generation, and database creation workflow.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.models.episode_character import EpisodeCharacter
from app.models.virtual_ip import VirtualIP
from app.services.script.character_background_generator import (
    generate_character_background,
)
from app.services.script.temporary_character_extractor import (
    TemporaryCharacterInfo,
    extract_temporary_characters,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def auto_create_episode_characters(
    *,
    db: "Session",
    episode_id: int,
    script_content: Dict[str, Any],
    unknown_names: List[str],
    user_id: int,
    ai_service: Optional[Any] = None,
    default_virtual_ip_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Automatically create Episode characters from script unknown_names.

    Workflow:
    1. Extract character information from script content
    2. Generate character backgrounds using AI (or heuristics)
    3. Assign default VirtualIP (create if needed)
    4. Create EpisodeCharacter records in database
    5. Return created character information

    Args:
        db: Database session
        episode_id: Episode ID to create characters for
        script_content: Script content with scenes, dialogues, stage_directions
        unknown_names: List of unknown character names from script validation
        user_id: User ID (owner of the characters)
        ai_service: Optional AI service for background generation
        default_virtual_ip_id: Optional default VirtualIP ID (created if None)

    Returns:
        List of dictionaries with created character information:
        [
            {
                "episode_character_id": 123,
                "character_name": "快递员",
                "virtual_ip_id": 999,
                "needs_customization": True,
                "generated_info": {...}
            },
            ...
        ]
    """
    if not unknown_names:
        logger.info("No unknown names to create characters for")
        return []

    logger.info(f"Auto-creating Episode characters for {len(unknown_names)} unknown names")

    # Step 1: Extract character information from script
    logger.debug("Extracting character information from script...")
    extracted_chars = extract_temporary_characters(
        script_content=script_content,
        unknown_names=unknown_names,
    )

    if not extracted_chars:
        logger.warning("No character information could be extracted from script")
        return []

    logger.info(f"Extracted information for {len(extracted_chars)} characters")

    # Step 2: Get or create default VirtualIP
    default_vip = _get_or_create_default_virtual_ip(
        db=db,
        user_id=user_id,
        virtual_ip_id=default_virtual_ip_id,
    )

    if not default_vip:
        logger.error("Failed to get or create default VirtualIP")
        return []

    logger.info(f"Using default VirtualIP ID: {default_vip.id}")

    # Step 3: Get scene context for AI generation
    scene_context = _extract_scene_context(script_content)

    # Step 4: Create EpisodeCharacter records
    created_characters: List[Dict[str, Any]] = []

    for char_info in extracted_chars:
        try:
            created = await _create_single_character(
                db=db,
                episode_id=episode_id,
                character_info=char_info,
                default_vip=default_vip,
                scene_context=scene_context,
                ai_service=ai_service,
            )

            if created:
                created_characters.append(created)

        except Exception as e:
            logger.error(
                f"Failed to create character '{char_info.character_name}': {e}",
                exc_info=True,
            )
            continue

    # Commit all changes
    try:
        db.commit()
        logger.info(f"Successfully created {len(created_characters)} Episode characters")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit Episode characters: {e}", exc_info=True)
        return []

    return created_characters


async def _create_single_character(
    *,
    db: "Session",
    episode_id: int,
    character_info: TemporaryCharacterInfo,
    default_vip: VirtualIP,
    scene_context: Dict[str, Any],
    ai_service: Optional[Any],
) -> Optional[Dict[str, Any]]:
    """Create a single Episode character with AI-generated background.

    Args:
        db: Database session
        episode_id: Episode ID
        character_info: Extracted character information
        default_vip: Default VirtualIP to assign
        scene_context: Scene context for AI generation
        ai_service: Optional AI service

    Returns:
        Dictionary with created character info, or None if creation failed
    """
    logger.debug(f"Creating character: {character_info.character_name}")

    # Generate character background with AI
    try:
        generated = await generate_character_background(
            character_info=character_info,
            scene_context=scene_context,
            ai_service=ai_service,
        )
    except Exception as e:
        logger.warning(
            f"Background generation failed for '{character_info.character_name}': {e}"
        )
        # Use empty fallback
        generated = {
            "personality": "",
            "background": "",
            "appearance_override": "",
        }

    # Infer importance from dialogue count
    importance = _infer_importance(character_info.dialogue_count)

    # Create EpisodeCharacter record
    episode_char = EpisodeCharacter(
        episode_id=episode_id,
        virtual_ip_id=default_vip.id,
        virtual_ip_business_id=default_vip.business_id,
        character_name=character_info.character_name,
        role_type="temporary",
        importance=importance,
        personality=generated.get("personality"),
        background=generated.get("background"),
        appearance_override=generated.get("appearance_override"),
        scene_appearances=character_info.scene_appearances,  # JSON list
        first_appearance_scene=character_info.first_appearance_scene,
        last_appearance_scene=character_info.last_appearance_scene,
        extra_metadata={
            "auto_created": True,
            "dialogue_count": character_info.dialogue_count,
            "appearance_hints": character_info.appearance_hints,
        },
    )

    db.add(episode_char)
    db.flush()  # Get ID without committing

    logger.info(
        f"Created EpisodeCharacter ID {episode_char.id}: {character_info.character_name}"
    )

    return {
        "episode_character_id": episode_char.id,
        "episode_character_business_id": episode_char.business_id,
        "character_name": character_info.character_name,
        "virtual_ip_id": default_vip.id,
        "importance": importance,
        "needs_customization": True,  # User should review and customize
        "generated_info": {
            "personality": generated.get("personality"),
            "background": generated.get("background"),
            "appearance_override": generated.get("appearance_override"),
            "scene_appearances": character_info.scene_appearances,
            "dialogue_count": character_info.dialogue_count,
        },
    }


def _get_or_create_default_virtual_ip(
    *,
    db: "Session",
    user_id: int,
    virtual_ip_id: Optional[int] = None,
) -> Optional[VirtualIP]:
    """Get existing or create default VirtualIP for temporary characters.

    Args:
        db: Database session
        user_id: User ID (owner)
        virtual_ip_id: Optional specific VirtualIP ID to use

    Returns:
        VirtualIP instance, or None if creation failed
    """
    # If specific VirtualIP ID provided, use it
    if virtual_ip_id:
        vip = db.query(VirtualIP).filter(
            VirtualIP.id == virtual_ip_id,
            VirtualIP.is_deleted == False,
        ).first()

        if vip:
            logger.debug(f"Using provided VirtualIP ID: {virtual_ip_id}")
            return vip
        else:
            logger.warning(f"Provided VirtualIP ID {virtual_ip_id} not found")

    # Try to find existing default VirtualIP for this user
    default_vip = db.query(VirtualIP).filter(
        VirtualIP.user_id == user_id,
        VirtualIP.name == "临时角色默认形象",
        VirtualIP.is_deleted == False,
    ).first()

    if default_vip:
        logger.debug(f"Using existing default VirtualIP ID: {default_vip.id}")
        return default_vip

    # Create new default VirtualIP
    logger.info("Creating new default VirtualIP for temporary characters")

    try:
        new_vip = VirtualIP(
            user_id=user_id,
            name="临时角色默认形象",
            description="用于Episode临时角色的默认形象，可后续替换为专用形象",
            personality="通用临时角色",
            background_story="临时角色默认背景",
            biography="",
            style_prompt="普通人物形象",
            voice_config={
                "provider": "minimax",
                "voice_id": "male-qn-qingse",  # Default voice
            },
        )

        db.add(new_vip)
        db.flush()

        logger.info(f"Created default VirtualIP ID: {new_vip.id}")
        return new_vip

    except Exception as e:
        logger.error(f"Failed to create default VirtualIP: {e}", exc_info=True)
        return None


def _extract_scene_context(script_content: Dict[str, Any]) -> Dict[str, Any]:
    """Extract scene context from script content for AI generation.

    Args:
        script_content: Script content dictionary

    Returns:
        Dictionary with setting_location, setting_time, etc.
    """
    # Try to get setting from metadata
    metadata = script_content.get("metadata", {})

    return {
        "setting_location": metadata.get("setting_location", ""),
        "setting_time": metadata.get("setting_time", ""),
    }


def _infer_importance(dialogue_count: int) -> int:
    """Infer character importance level from dialogue count.

    Args:
        dialogue_count: Number of dialogue lines

    Returns:
        Importance level (1-5)
    """
    if dialogue_count >= 10:
        return 3  # Important temporary character
    elif dialogue_count >= 5:
        return 2  # Moderate importance
    else:
        return 1  # Minor character
