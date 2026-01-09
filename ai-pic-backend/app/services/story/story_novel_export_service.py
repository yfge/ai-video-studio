from __future__ import annotations

from typing import Any, Callable, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.script import Story
from app.models.user import User

from .story_novel_export_payload import build_story_novel_payload
from .story_novel_export_utils import StoryNovelExportResult, estimate_chapter_count
from .story_novel_export_zhihu import export_zhihu_novel_to_file

ProgressCallback = Callable[[str], Any]


def _resolve_model(model_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if model_id and ":" in model_id:
        prefer_provider, resolved = model_id.split(":", 1)
        return prefer_provider, resolved
    return None, model_id


class StoryNovelExportService:
    """Export Story into a long-form Zhihu-style novel text."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_story_for_user(self, story_business_id: str, user: User) -> Story:
        query = self.db.query(Story).filter(
            Story.is_deleted.is_(False), Story.business_id == story_business_id
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(Story.user_id == user.id)
        story = query.first()
        if not story:
            raise HTTPException(status_code=404, detail="故事不存在")
        return story

    async def export_zhihu_novel(
        self,
        *,
        story: Story,
        target_words: int,
        chapter_count: Optional[int],
        model: Optional[str],
        temperature: float,
        progress: ProgressCallback | None = None,
    ) -> StoryNovelExportResult:
        """Generate a Zhihu-style novel and persist it as a downloadable text file."""

        prefer_provider, model_id = _resolve_model(model)
        chapter_total = estimate_chapter_count(target_words, chapter_count)
        story_payload = build_story_novel_payload(self.db, story=story)
        return await export_zhihu_novel_to_file(
            story_title=story.title,
            story_payload=story_payload,
            target_words=target_words,
            chapter_total=chapter_total,
            model_id=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=progress,
        )
