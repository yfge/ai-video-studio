from __future__ import annotations

import json

from app.core.celery_app import celery_app
from app.models.task import Task, TaskType
from app.services.story.story_novel_revision_service import StoryNovelRevisionService


def queue_initial_novel_generation(db, user, story, request):
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
        revision = StoryNovelRevisionService(db, user).create_draft(
            story.business_id, request, task_id=task.id
        )
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
        },
    }


def queue_novel_operation(db, user, revision, operation: str, **payload):
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
