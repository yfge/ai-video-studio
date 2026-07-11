from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.models.video_generation_task import VideoGenerationTask
from app.repositories.script_repository import ScriptRepository
from app.services.storyboard.candidate_lineage import record_canvas_candidate_lineage
from app.services.video.video_task_utils import merge_urls


def apply_storyboard_result(
    db,
    item: VideoGenerationTask,
    result_payload: Dict[str, Any],
    params: Dict[str, Any],
) -> None:
    context = _load_storyboard_context(db, item)
    if not context:
        return
    script, storyboard, frames, idx, frame = context
    updated_frame = _build_updated_frame(frame, item, result_payload, params)
    frames[idx] = updated_frame
    _persist_storyboard(db, script.id, storyboard, frames)


def _load_storyboard_context(
    db, item: VideoGenerationTask
) -> Optional[Tuple[Any, Dict[str, Any], list, int, Dict[str, Any]]]:
    script = ScriptRepository(db).get_by_id(item.script_id)
    if not script:
        return None
    extra_raw = script.extra_metadata or {}
    storyboard = dict(extra_raw.get("storyboard") or {})
    frames = list(storyboard.get("frames") or [])
    idx = int(item.frame_index)
    if idx < 0 or idx >= len(frames):
        return None
    frame = dict(frames[idx]) if isinstance(frames[idx], dict) else {}
    return script, storyboard, frames, idx, frame


def _build_updated_frame(
    frame: Dict[str, Any],
    item: VideoGenerationTask,
    result_payload: Dict[str, Any],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    frame["video_url"] = result_payload.get("video_url")
    frame["video_url_original"] = result_payload.get("original_video_url")
    frame["video_thumbnail_url"] = result_payload.get("thumbnail_url")
    frame["video_thumbnail_url_original"] = result_payload.get("original_thumbnail_url")
    frame["video_last_frame_url"] = result_payload.get("last_frame_url")
    frame["video_last_frame_url_original"] = result_payload.get(
        "original_last_frame_url"
    )

    frame["video_urls"] = merge_urls(frame.get("video_urls"), frame.get("video_url"))
    frame["video_thumbnail_urls"] = merge_urls(
        frame.get("video_thumbnail_urls"), frame.get("video_thumbnail_url")
    )
    frame["video_last_frame_urls"] = merge_urls(
        frame.get("video_last_frame_urls"), frame.get("video_last_frame_url")
    )

    frame["video_generation"] = {
        "duration": result_payload.get("duration"),
        "provider": result_payload.get("provider_used") or item.provider,
        "model": result_payload.get("model_used") or item.model,
        "method": result_payload.get("generation_method"),
        "prompt": params.get("prompt"),
        "resolution": params.get("resolution"),
        "ratio": params.get("ratio"),
        "start_image_url": params.get("image_url"),
        "end_image_url": params.get("end_image_url"),
        "thumbnail_url": result_payload.get("thumbnail_url"),
        "last_frame_url": result_payload.get("last_frame_url"),
    }
    if isinstance(params.get("canvas_branch"), dict) and item.task_id is not None:
        record_canvas_candidate_lineage(
            frame,
            [frame["video_url"]] if frame.get("video_url") else [],
            params["canvas_branch"],
            task_id=int(item.task_id),
        )
    return frame


def _persist_storyboard(
    db,
    script_id: int,
    storyboard: Dict[str, Any],
    frames: list,
) -> None:
    storyboard["frames"] = frames
    ScriptRepository(db).update_storyboard(
        script_id, storyboard, increment_version=False
    )
    db.commit()
