from __future__ import annotations

from typing import Any, Dict, Optional

from app.schemas.context_pack import (
    ContextPackBudget,
    EpisodeContextPack,
    StoryContextPack,
)
from app.services.context_pack.story_context_pack_builder import (
    build_story_context_pack,
)
from sqlalchemy.orm import Session


def build_episode_context_pack(
    *,
    db: Session,
    story_id: int,
    story_snapshot: Dict[str, Any],
    continuity_ledger: Optional[Dict[str, Any]],
    generation_params: Optional[Dict[str, Any]],
    episode_number: Optional[int],
    budget: Optional[ContextPackBudget] = None,
) -> Dict[str, Any]:
    """Build an EpisodeContextPack.

    For Phase 2 we keep this minimal: StoryContextPack + target episode number.
    """
    story_pack = build_story_context_pack(
        db=db,
        story_id=story_id,
        story_snapshot=story_snapshot,
        continuity_ledger=continuity_ledger,
        generation_params=generation_params,
        budget=budget,
    )
    return EpisodeContextPack(
        story=StoryContextPack.model_validate(story_pack),
        episode_number=episode_number,
        episode_id=None,
    ).model_dump()
