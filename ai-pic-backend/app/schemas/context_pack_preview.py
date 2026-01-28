from __future__ import annotations

from typing import Optional

from app.schemas.context_pack import ContextPackBudget
from app.schemas.generation_requests import EpisodeGenerationRequest
from pydantic import Field


class EpisodeContextPackPreviewRequest(EpisodeGenerationRequest):
    """Preview request for building the episode generation Context Pack.

    We extend EpisodeGenerationRequest so the preview uses the same market/micro-genre
    overrides that will be applied during episode generation.
    """

    budget: Optional[ContextPackBudget] = None
    include_continuity_ledger: bool = Field(
        True, description="Include continuity ledger"
    )
    include_character_cards: bool = Field(True, description="Include character cards")
    include_recent_episodes: bool = Field(
        True, description="Include recent episode summaries"
    )
