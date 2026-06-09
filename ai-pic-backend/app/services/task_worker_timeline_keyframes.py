from __future__ import annotations

from typing import Any, Dict

import anyio
from app.core.celery_app import celery_app


@celery_app.task(name="tasks.timeline_clip_keyframe_generate")
def timeline_clip_keyframe_generate_task(
    task_id: int,
    payload: Dict[str, Any],
    user_id: int | None = None,
) -> None:
    from app.core.database import get_task_db
    from app.services.timeline_clip_keyframe_processor import (
        TimelineClipKeyframeProcessor,
    )

    with get_task_db() as db:
        processor = TimelineClipKeyframeProcessor(db)
        anyio.run(processor.process_keyframe_task, task_id, payload, user_id)
