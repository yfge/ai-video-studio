from __future__ import annotations

from typing import Any, Dict, Optional

import anyio
from app.services.video.video_duration import normalize_target_seconds
from app.services.video.video_task_dispatcher import VideoTaskDispatcher


def resolve_target_duration_seconds(frame: Dict[str, Any], opts: Dict[str, Any]) -> float:
    override = opts.get("duration")
    if override is not None:
        return normalize_target_seconds(override)

    start_ms = frame.get("start_ms")
    end_ms = frame.get("end_ms")
    try:
        if start_ms is not None and end_ms is not None:
            start_ms_int = int(start_ms)
            end_ms_int = int(end_ms)
            if end_ms_int >= start_ms_int:
                return normalize_target_seconds((end_ms_int - start_ms_int) / 1000.0)
    except Exception:
        pass

    return normalize_target_seconds(frame.get("duration_seconds") or 5.0)


def submit_provider_task(
    dispatcher: VideoTaskDispatcher,
    *,
    prompt: Optional[str],
    start_url: Optional[str],
    end_url: Optional[str],
    duration: int,
    opts: Dict[str, Any],
) -> Any:
    payload = {
        "prompt": prompt,
        "image_url": start_url,
        "end_image_url": end_url,
        "model": opts.get("model"),
        "prefer_provider": None,
        "duration": duration,
        "fps": opts["fps"],
        "resolution": opts["resolution"],
        "ratio": opts.get("ratio"),
        "watermark": opts.get("watermark"),
        "seed": opts.get("seed"),
        "camera_fixed": opts.get("camera_fixed"),
        "camera_control": opts.get("camera_control"),
        "service_tier": opts.get("service_tier"),
        "execution_expires_after": opts.get("execution_expires_after"),
        "return_last_frame": opts.get("return_last_frame"),
    }

    # anyio.run() only supports positional args, so wrap the kwarg call.
    async def _submit() -> Any:
        return await dispatcher.submit_video_task(**payload)

    return anyio.run(_submit)
