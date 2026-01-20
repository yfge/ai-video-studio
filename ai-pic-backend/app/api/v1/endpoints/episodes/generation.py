"""
Episode generation endpoints.

AI-powered episode generation from story data.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.schemas.script import EpisodeResponse
from app.services.episode.episode_generation_service import EpisodeGenerationService

# Backward-compat export for tests/legacy callers (they monkeypatch this name).
ai_service = None  # type: ignore[assignment]

router = APIRouter()


@router.post("/generate", response_model=List[EpisodeResponse])
async def generate_episodes(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate episodes using AI."""
    service = EpisodeGenerationService(db, current_user)
    created = await service.generate_episodes(request)
    return [EpisodeResponse.from_orm(episode) for episode in created]


@router.post("/prompt/preview")
async def preview_episode_prompt(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the final prompt for episode generation (without calling model)."""
    service = EpisodeGenerationService(db, current_user)
    prompt = service.build_preview_prompt(request)
    return {"success": True, "data": {"prompt": prompt}}
