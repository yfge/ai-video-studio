from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from app.schemas.generation import ScriptScoreResult
from app.services.scoring.script_score_service import ScriptScoreService

if TYPE_CHECKING:
    from app.services.ai_service import AIService


async def score_script_from_db(
    ai_service: "AIService",
    script_id: int,
    db_session: Any,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
) -> ScriptScoreResult:
    """Load a script and run ScriptScore with story and episode context."""
    from app.models.script import Script

    script = db_session.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise ValueError(f"Script {script_id} not found")

    episode = getattr(script, "episode", None)
    story = getattr(episode, "story", None) if episode else None

    story_ctx = None
    if story:
        extra = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
        story_ctx = {
            "title": story.title,
            "genre": story.genre,
            "market_region": extra.get("market_region"),
            "micro_genre": extra.get("micro_genre"),
        }

    episode_ctx = None
    if episode:
        episode_ctx = {
            "episode_number": episode.episode_number,
            "title": episode.title,
            "summary": episode.summary,
        }

    service = ScriptScoreService(ai_service)
    return await service.score_script(
        script_content=script.content or "",
        story=story_ctx,
        episode=episode_ctx,
        scenes=script.scenes or [],
        dialogues=script.dialogues or [],
        prefer_provider=prefer_provider,
        prefer_model=prefer_model,
    )
