from __future__ import annotations

from app.models.story_novel_export import StoryNovelExport
from app.schemas.generation_requests import StoryNovelExportRequest

from .story_novel_export_service import StoryNovelExportService
from .story_novel_export_utils import build_export_result_path


async def run_legacy_export(db, task, payload, user) -> None:
    request = StoryNovelExportRequest(**(payload.get("request") or {}))
    service = StoryNovelExportService(db)
    story = service.get_story_for_user(payload["story_business_id"], user)

    def update_progress(message: str) -> None:
        task.description = message
        db.commit()

    result = await service.export_zhihu_novel(
        story=story,
        target_words=request.target_words,
        chapter_count=request.chapter_count,
        model=request.model,
        temperature=request.temperature or 0.7,
        progress=update_progress,
    )
    db.add(
        StoryNovelExport(
            story_id=story.id,
            story_business_id=story.business_id,
            task_id=task.id,
            user_id=user.id,
            style="zhihu",
            target_words=request.target_words,
            chapter_count=result.chapter_count,
            total_words=result.total_words,
            model=request.model,
            temperature=request.temperature,
            file_relative_path=result.relative_path,
            content_text=result.content_text,
            lifecycle_status="legacy",
        )
    )
    task.result_file_path = build_export_result_path(result.relative_path)
