"""Volcengine video task response helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.providers.polling_utils import TaskStatus


def map_status(value: str) -> TaskStatus:
    status = (value or "").lower()
    if status == "succeeded":
        return TaskStatus.SUCCESS
    if status in {"failed", "canceled", "cancelled", "expired"}:
        return TaskStatus.FAILED
    if status in {"queued", "running", "processing", "pending"}:
        return TaskStatus.PROCESSING
    return TaskStatus.PENDING


def extract_task_id(data: Dict[str, Any]) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    task_id = data.get("id") or data.get("task_id")
    if task_id:
        return str(task_id)
    nested = data.get("data")
    if isinstance(nested, dict):
        nested_id = nested.get("id") or nested.get("task_id")
        return str(nested_id) if nested_id else None
    return None


def extract_error(data: Dict[str, Any]) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    err = data.get("error") or {}
    if not isinstance(err, dict):
        return str(err) if err else None
    return err.get("message") or err.get("code")


def extract_output_urls(data: Dict[str, Any]) -> Dict[str, Any]:
    content = _normalize_content(data.get("content"))
    video_url = (
        content.get("video_url")
        or content.get("videoUrl")
        or content.get("url")
        or data.get("video_url")
        or data.get("videoUrl")
        or data.get("url")
    )
    thumbnail_url = (
        content.get("thumbnail_url")
        or content.get("cover_image_url")
        or content.get("cover_url")
        or content.get("poster_url")
    )
    last_frame_url = content.get("last_frame_url") or content.get("lastFrameUrl")
    return {
        "video_url": video_url,
        "thumbnail_url": thumbnail_url,
        "last_frame_url": last_frame_url,
    }


def _normalize_content(content: Any) -> Dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        merged: Dict[str, Any] = {}
        for item in content:
            if not isinstance(item, dict):
                continue
            nested = item.get("video_url") or item.get("image_url")
            if isinstance(nested, dict):
                merged.update(nested)
            merged.update(item)
        return merged
    return {}
