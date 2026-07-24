from __future__ import annotations

import json

from app.core.celery_app import celery_app
from app.models.task import Task, TaskType
from app.repositories.story_novel_repository import StoryNovelRepository
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from fastapi import HTTPException


def queue_initial_novel_generation(db, user, story, request):
    service = StoryNovelRevisionService(db, user)
    story = StoryNovelRepository(db).accessible_story_by_id(
        story.id, user, for_update=True
    )
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    service._ensure_story_idle(story)
    if request.style == "prose" and (story.story_seed or {}).get("schema") != (
        "story_seed_v2"
    ):
        raise HTTPException(
            status_code=409,
            detail="请先将文字大纲结构化并确认 story_seed_v2",
        )
    task = Task(
        title=f"生成小说 - {story.title}",
        description="等待生成…",
        task_type=TaskType.TEXT_GENERATION,
        prompt=f"Novel export: {story.title}",
        parameters=json.dumps(request.model_dump(), ensure_ascii=False),
        user_id=user.id,
        target_business_id=story.business_id,
    )
    db.add(task)
    db.flush()
    payload = {"story_business_id": story.business_id, "request": request.model_dump()}
    revision = None
    if request.style == "prose":
        revision = service.create_draft(story.business_id, request, task_id=task.id)
        task.target_business_id = revision.business_id
        payload.update(
            operation="generate_revision",
            revision_business_id=revision.business_id,
        )
    db.commit()
    db.refresh(task)
    celery_app.send_task("tasks.story_novel_generate", args=[task.id, payload, user.id])
    return {
        "success": True,
        "data": {
            "task_id": task.id,
            "status": task.status,
            "revision_business_id": revision.business_id if revision else None,
            "warnings": request.compatibility_warnings,
        },
    }


def queue_novel_operation(db, user, revision, operation: str, **payload):
    service = StoryNovelRevisionService(db, user)
    repo = StoryNovelRepository(db)
    story = repo.accessible_story_by_id(revision.story_id, user, for_update=True)
    revision = repo.accessible_revision(
        revision.business_id,
        user,
        with_chapters=False,
        for_update=True,
    )
    if not story or not revision:
        raise HTTPException(status_code=404, detail="小说版本不存在")
    service.ensure_no_active_task(revision)
    task = Task(
        title=f"小说任务 - {revision.story.title}",
        description="等待处理…",
        task_type=TaskType.TEXT_GENERATION,
        prompt=operation,
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user.id,
        target_business_id=revision.business_id,
    )
    db.add(task)
    db.flush()
    revision.task_id = task.id
    db.commit()
    db.refresh(task)
    celery_app.send_task(
        "tasks.story_novel_generate",
        args=[
            task.id,
            {
                "operation": operation,
                "revision_business_id": revision.business_id,
                **payload,
            },
            user.id,
        ],
    )
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def queue_story_seed_structure(db, user, story):
    service = StoryNovelRevisionService(db, user)
    story = StoryNovelRepository(db).accessible_story_by_id(
        story.id, user, for_update=True
    )
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    service._ensure_story_idle(story)
    task = Task(
        title=f"结构化大纲 - {story.title}",
        description="等待规划…",
        task_type=TaskType.TEXT_GENERATION,
        prompt="structure_story_seed",
        parameters=json.dumps(
            {"story_seed_version": int(story.story_seed_version or 1)},
            ensure_ascii=False,
        ),
        user_id=user.id,
        target_business_id=story.business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    celery_app.send_task(
        "tasks.story_novel_generate",
        args=[
            task.id,
            {
                "operation": "structure_story_seed",
                "story_business_id": story.business_id,
                "story_seed_version": int(story.story_seed_version or 1),
            },
            user.id,
        ],
    )
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
