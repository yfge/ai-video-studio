"""Small read helpers used by script generation services."""

from __future__ import annotations

from typing import Any


def fetch_episode_character_sources(db: Any, episode_id: int):
    """Return episode character rows paired with their VirtualIP row."""
    from app.models.episode_character import EpisodeCharacter
    from app.models.virtual_ip import VirtualIP

    episode_chars = (
        db.query(EpisodeCharacter)
        .filter(
            EpisodeCharacter.episode_id == episode_id,
            EpisodeCharacter.is_deleted.is_(False),
        )
        .all()
    )
    if not episode_chars:
        return []

    vip_ids = {ec.virtual_ip_id for ec in episode_chars}
    vips = db.query(VirtualIP).filter(VirtualIP.id.in_(vip_ids)).all()
    vip_by_id = {vip.id: vip for vip in vips}
    return [(ec, vip_by_id.get(ec.virtual_ip_id)) for ec in episode_chars]


def fetch_episode_story_user_id(db: Any, episode_id: int):
    """Return the owning story user id for an episode, when available."""
    from app.models.script import Episode as EpisodeModel

    episode_record = (
        db.query(EpisodeModel).filter(EpisodeModel.id == episode_id).first()
    )
    if episode_record and episode_record.story:
        return episode_record.story.user_id
    return None
