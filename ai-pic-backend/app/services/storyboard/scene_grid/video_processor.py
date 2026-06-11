"""Grid-to-continuous-video generation for scene grid storyboards."""

from __future__ import annotations

from typing import Any, Dict

from app.repositories.storyboard_media_repository import (
    get_script_by_id,
    load_scene_grids,
    save_scene_grid,
)
from app.services.storyboard.scene_grid.prompt_builder import (
    build_video_prompt,
    clamp_total_duration,
)
from app.services.storyboard.scene_grid.shared import (
    abs_url,
    load_ref_context,
    utc_now,
)


async def generate_video(db, task_id: int, payload: Dict[str, Any]) -> None:
    from app.services.ai_service import ai_service
    from app.services.video.video_generation_service import VideoGenerationService

    script_id = int(payload["script_id"])
    scene_number = int(payload["scene_number"])
    script = get_script_by_id(db, script_id)
    if not script:
        raise RuntimeError("剧本不存在")
    grid = load_scene_grids(db, script_id).get(str(scene_number))
    if not isinstance(grid, dict) or not grid.get("image_url"):
        raise RuntimeError(f"场景 {scene_number} 尚未生成宫格分镜图")

    cells = [cell for cell in grid.get("cells") or [] if isinstance(cell, dict)]
    durations = [float(cell.get("duration") or 0) or 1.2 for cell in cells] or [1.2]
    duration = int(payload.get("duration") or 0) or clamp_total_duration(durations)

    override = str(payload.get("prompt") or "").strip()
    if override:
        prompt_data = {"video_prompt": override, "prompt_source": "user_override"}
    else:
        ref_ctx = load_ref_context(db, script, script_id)
        prompt_data = await build_video_prompt(
            script,
            scene_number,
            cells,
            ref_ctx,
            total_duration=duration,
            aspect_ratio=str(grid.get("aspect_ratio") or "16:9"),
            style=payload.get("style"),
            ai_manager=getattr(ai_service, "ai_manager", None),
        )

    video_service = VideoGenerationService(
        ai_manager=getattr(ai_service, "ai_manager", None)
    )
    extra_kwargs: Dict[str, Any] = {}
    if payload.get("generate_audio") is not None:
        extra_kwargs["generate_audio"] = bool(payload.get("generate_audio"))
    if payload.get("ratio"):
        extra_kwargs["ratio"] = payload.get("ratio")
    result = await video_service.generate_video(
        prompt=prompt_data["video_prompt"],
        image_url=abs_url(str(grid["image_url"])),
        model=payload.get("model") or "seedance-2.0",
        duration=duration,
        resolution=str(payload.get("resolution") or "720p"),
        **extra_kwargs,
    )
    if not result.get("success"):
        raise RuntimeError(result.get("error") or "宫格成片生成失败")

    save_scene_grid(
        db,
        script_id=script_id,
        scene_number=scene_number,
        grid_payload={
            "video_prompt": prompt_data["video_prompt"],
            "video_prompt_source": prompt_data["prompt_source"],
            "video_url": result.get("video_url") or result.get("oss_url"),
            "video_thumbnail_url": result.get("thumbnail_url"),
            "video_model": result.get("model_used") or payload.get("model"),
            "video_provider": result.get("provider_used"),
            "video_duration": duration,
            "video_generated_at": utc_now(),
        },
    )
