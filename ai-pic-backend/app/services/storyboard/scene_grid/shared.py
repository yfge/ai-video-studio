"""Shared helpers for scene grid processors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def load_ref_context(db, script, script_id: int):
    # Reuses the storyboard image task's reference loader; task workers already
    # import api-layer processors in this codebase (see task_worker.py).
    from app.api.v1.endpoints.storyboard.image_task_refs import load_image_ref_context

    return load_image_ref_context(db, script, script_id)


def abs_url(url: str) -> str:
    from app.api.v1.endpoints.storyboard.frame_utils import _abs_url

    return _abs_url(url)


def to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
