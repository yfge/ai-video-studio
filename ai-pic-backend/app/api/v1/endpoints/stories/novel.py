from __future__ import annotations

from pathlib import Path

from app.api.v1.endpoints.stories.novel_task_queue import queue_initial_novel_generation
from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import TaskStatus
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from app.schemas.story_novel_export import (
    StoryNovelExportListResponse,
    StoryNovelExportSummary,
)
from app.services.story.story_novel_export_service import StoryNovelExportService
from app.services.story.story_novel_export_utils import (
    parse_export_result_path,
    safe_join_under,
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/business/{story_business_id}/novel/generate-async")
async def generate_story_novel_async(
    story_business_id: str,
    request: StoryNovelExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue a legacy export or create a checkpointed prose revision."""
    service = StoryNovelExportService(db)
    story = service.get_story_for_user(story_business_id, current_user)

    return queue_initial_novel_generation(db, current_user, story, request)


@router.get("/novel/tasks/{task_id}/download")
def download_story_novel_export(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """下载已生成的知乎体小说导出文件。"""
    repo = StoryNovelRepository(db)
    task = repo.accessible_task(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务未完成")

    relative_path = parse_export_result_path(task.result_file_path or "")
    if relative_path:
        file_path = safe_join_under(Path(settings.UPLOAD_DIR), relative_path)
        if file_path.exists():
            return FileResponse(
                str(file_path),
                filename=file_path.name,
                media_type="text/plain; charset=utf-8",
            )

    export_row = repo.export_by_task(task_id, current_user)
    if not export_row:
        raise HTTPException(status_code=404, detail="导出内容不存在")

    filename = "zhihu_novel.txt"
    if export_row.file_relative_path:
        filename = Path(export_row.file_relative_path).name or filename

    return Response(
        content=export_row.content_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/business/{story_business_id}/novel/exports",
    response_model=StoryNovelExportListResponse,
)
def list_story_novel_exports(
    story_business_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """列出故事的小说导出历史（用于刷新后恢复查看/下载入口）。"""
    service = StoryNovelExportService(db)
    story = service.get_story_for_user(story_business_id, current_user)

    resolved_limit = max(1, min(limit, 50))
    exports = StoryNovelRepository(db).list_exports(
        story.id, current_user, resolved_limit
    )
    return {"items": [StoryNovelExportSummary.model_validate(row) for row in exports]}
