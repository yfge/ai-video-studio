"""Celery task registration for Timeline grid-storyboard generation."""

from __future__ import annotations

import anyio

from app.core.celery_app import celery_app
from app.core.database import get_task_db
from app.services.storyboard.grid_storyboard_sheet_processor import (
    GridStoryboardSheetProcessor,
)


@celery_app.task(name="tasks.grid_storyboard_sheet_generate")
def grid_storyboard_sheet_generate_task(
    task_id: int,
    payload: dict,
    user_id: int | None = None,
) -> None:
    """Generate and persist one Timeline-derived grid storyboard sheet."""

    with get_task_db() as db:
        processor = GridStoryboardSheetProcessor(db)
        anyio.run(processor.process_grid_sheet_task, task_id, payload, user_id)
