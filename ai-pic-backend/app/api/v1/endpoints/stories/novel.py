from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.middleware import get_current_active_user
from app.models.story_novel_export import StoryNovelExport
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.generation_requests import StoryNovelExportRequest
from app.schemas.story_novel_export import (
    StoryNovelExportListResponse,
    StoryNovelExportSummary,
)
from app.services.story.story_novel_export_service import StoryNovelExportService
from app.services.story.story_novel_export_utils import (
    build_export_result_path,
    parse_export_result_path,
    safe_join_under,
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

router = APIRouter()


def process_story_novel_export_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker entrypoint: generate Zhihu-style novel export and persist file."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            task.description = "开始生成知乎体小说…"
            db.commit()

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        story_business_id = str(payload.get("story_business_id") or "").strip()
        if not story_business_id:
            raise HTTPException(status_code=400, detail="缺少 story_business_id")

        request_dict = payload.get("request") or {}
        export_request = StoryNovelExportRequest(**request_dict)
        temperature_value = (
            0.7 if export_request.temperature is None else export_request.temperature
        )

        service = StoryNovelExportService(db)
        story = service.get_story_for_user(story_business_id, user)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task and story and not task.target_business_id:
            task.target_business_id = story.business_id
            db.commit()

        def _progress(message: str) -> None:
            task_row = db.query(Task).filter(Task.id == task_id).first()
            if not task_row:
                return
            task_row.description = message
            db.commit()

        import anyio

        async def _run():
            return await service.export_zhihu_novel(
                story=story,
                target_words=export_request.target_words,
                chapter_count=export_request.chapter_count,
                model=export_request.model,
                temperature=temperature_value,
                progress=_progress,
            )

        result = anyio.run(_run)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            export_row = StoryNovelExport(
                story_id=story.id,
                story_business_id=story.business_id,
                task_id=task.id,
                user_id=user.id,
                style=export_request.style,
                target_words=export_request.target_words,
                chapter_count=result.chapter_count,
                total_words=result.total_words,
                model=export_request.model,
                temperature=temperature_value,
                file_relative_path=result.relative_path,
                content_text=result.content_text,
            )
            db.add(export_row)

            task.status = TaskStatus.COMPLETED
            task.result_file_path = build_export_result_path(result.relative_path)
            task.description = (
                f"完成：约 {result.total_words} 字（{result.chapter_count} 章）"
            )
            db.commit()
    except Exception as exc:
        error_message = str(exc)
        if not error_message and isinstance(exc, HTTPException):
            error_message = str(exc.detail)
        if not error_message:
            error_message = repr(exc)
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.description = "生成失败"
            db.commit()
    finally:
        db.close()


@router.post("/business/{story_business_id}/novel/generate-async")
async def generate_story_novel_async(
    story_business_id: str,
    request: StoryNovelExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步导出知乎体小说：创建任务并交给 Celery worker 生成文本文件。"""
    service = StoryNovelExportService(db)
    story = service.get_story_for_user(story_business_id, current_user)

    task = Task(
        title=f"导出知乎体小说 - {story.title}",
        description="等待生成…",
        task_type=TaskType.TEXT_GENERATION,
        prompt=f"Zhihu novel export: {story.title}",
        parameters=json.dumps(request.model_dump(), ensure_ascii=False),
        user_id=current_user.id,
        target_business_id=story.business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_app.send_task(
        "tasks.story_novel_generate",
        args=[
            task.id,
            {"story_business_id": story_business_id, "request": request.model_dump()},
            current_user.id,
        ],
    )

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.get("/novel/tasks/{task_id}/download")
def download_story_novel_export(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """下载已生成的知乎体小说导出文件。"""
    query = db.query(Task).filter(Task.id == task_id)
    if not (current_user.is_admin or current_user.is_superuser):
        query = query.filter(Task.user_id == current_user.id)
    task = query.first()
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

    export_query = db.query(StoryNovelExport).filter(
        StoryNovelExport.task_id == task_id,
        StoryNovelExport.is_deleted.is_(False),
    )
    if not (current_user.is_admin or current_user.is_superuser):
        export_query = export_query.filter(StoryNovelExport.user_id == current_user.id)
    export_row = export_query.order_by(StoryNovelExport.id.desc()).first()
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

    query = db.query(StoryNovelExport).filter(
        StoryNovelExport.is_deleted.is_(False),
        StoryNovelExport.story_id == story.id,
    )
    if not (current_user.is_admin or current_user.is_superuser):
        query = query.filter(StoryNovelExport.user_id == current_user.id)

    resolved_limit = max(1, min(limit, 50))
    exports = query.order_by(StoryNovelExport.id.desc()).limit(resolved_limit).all()
    return {"items": [StoryNovelExportSummary.model_validate(row) for row in exports]}
