from __future__ import annotations

import json

from app.models.video_generation_task import VideoGenerationTask


def log_pending_tasks(
    logger, pending: list[VideoGenerationTask], limit: int
) -> None:
    payload = [
        {
            "id": item.id,
            "task_id": item.task_id,
            "script_id": item.script_id,
            "frame_index": item.frame_index,
            "provider": item.provider,
            "provider_task_id": item.provider_task_id,
            "status": item.status.value if item.status else None,
            "model_type": item.model_type,
            "model": item.model,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            "last_polled_at": item.last_polled_at.isoformat() if item.last_polled_at else None,
        }
        for item in pending
    ]

    logger.info(
        "Video task poll query result: %s",
        json.dumps({"limit": limit, "count": len(pending), "items": payload}, ensure_ascii=False),
    )

