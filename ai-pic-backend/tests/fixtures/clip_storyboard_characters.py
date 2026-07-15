from app.models.episode_character import EpisodeCharacter
from app.models.script import StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage


def add_story_character(
    db_session,
    story_id: int,
    user_id: int,
    name: str,
) -> VirtualIP:
    virtual_ip = _add_virtual_ip(db_session, user_id, name, "linwan")
    db_session.add(
        StoryCharacter(
            story_id=story_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="protagonist",
            importance=5,
        )
    )
    db_session.commit()
    db_session.refresh(virtual_ip)
    return virtual_ip


def add_episode_character(
    db_session,
    episode_id: int,
    user_id: int,
    name: str,
) -> VirtualIP:
    slug = "courier" if name == "快递员" else name
    virtual_ip = _add_virtual_ip(db_session, user_id, name, slug)
    db_session.add(
        EpisodeCharacter(
            episode_id=episode_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="temporary",
            importance=3,
        )
    )
    db_session.commit()
    db_session.refresh(virtual_ip)
    return virtual_ip


def _add_virtual_ip(
    db_session,
    user_id: int,
    name: str,
    slug: str,
) -> VirtualIP:
    virtual_ip = VirtualIP(
        user_id=user_id,
        name=name,
        description=f"{name} character profile",
        style_prompt=f"{name} visual style",
    )
    db_session.add(virtual_ip)
    db_session.flush()
    db_session.add(
        VirtualIPImage(
            virtual_ip_id=virtual_ip.id,
            filename=f"{slug}.png",
            original_filename=f"{slug}.png",
            file_path=f"/uploads/{slug}.png",
            oss_url=f"https://cdn.example/{slug}.png",
            file_size=123,
            mime_type="image/png",
            category="avatar",
            is_default=True,
        )
    )
    return virtual_ip
