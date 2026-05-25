"""Celery task registration for Timeline render jobs."""

from __future__ import annotations

import anyio

from app.core.celery_app import celery_app
from app.core.database import get_task_db
from app.services.render.timeline_render_service import TimelineRenderService


@celery_app.task(name="tasks.timeline_render")
def timeline_render_task(render_job_id: int, user_id: int | None = None) -> None:
    """Execute a queued Timeline render job."""

    with get_task_db() as db:
        service = TimelineRenderService(db)
        anyio.run(service.process_render_job, render_job_id, user_id)
