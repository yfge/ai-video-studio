"""Task processors for scene grid sheet and grid-to-video generation."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.task import TaskStatus
from app.repositories.storyboard_media_repository import (
    get_script_by_id,
    get_task_by_id,
    load_storyboard_frames,
    save_scene_grid,
)
from app.services.storyboard.scene_grid.layout import scene_grid_layout
from app.services.storyboard.scene_grid.prompt_builder import (
    build_sheet_prompt,
    cell_durations,
)
from app.services.storyboard.scene_grid.refs import resolve_reference_images
from app.services.storyboard.scene_grid.shared import (
    load_ref_context,
    to_int,
    utc_now,
)
from app.services.storyboard.scene_grid.video_processor import generate_video

logger = get_logger("storyboard_scene_grid")


async def process_scene_grid_sheet_task(
    db, task_id: int, payload: Dict[str, Any], user_id: Optional[int]
) -> None:
    """Generate one scene grid storyboard sheet and persist it on the script."""
    await _run_with_task_status(db, task_id, _generate_sheet, payload, user_id)


async def process_scene_grid_video_task(
    db, task_id: int, payload: Dict[str, Any], user_id: Optional[int]
) -> None:
    """Generate a continuous video from the scene grid sheet via Seedance."""

    async def _video(db_, task_id_, payload_, _user_id):
        await generate_video(db_, task_id_, payload_)

    await _run_with_task_status(db, task_id, _video, payload, user_id)


async def _run_with_task_status(db, task_id, fn, payload, user_id) -> None:
    task = get_task_by_id(db, task_id)
    try:
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()
        await fn(db, task_id, payload, user_id)
        if task:
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("scene grid task %s failed: %s", task_id, exc)
        task = get_task_by_id(db, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()


async def _generate_sheet(
    db, task_id: int, payload: Dict[str, Any], user_id: Optional[int]
) -> None:
    from app.services.ai_service import ai_service
    from app.services.storyboard.storyboard_image_generation import (
        generate_storyboard_image_urls,
    )

    script_id = int(payload["script_id"])
    scene_number = int(payload["scene_number"])
    script = get_script_by_id(db, script_id)
    if not script:
        raise RuntimeError("剧本不存在")
    frames = [
        frame
        for frame in load_storyboard_frames(db, script_id)
        if to_int(frame.get("scene_number")) == scene_number
    ]
    if not frames:
        raise RuntimeError(f"场景 {scene_number} 没有分镜帧，请先生成分镜")

    ref_ctx = load_ref_context(db, script, script_id)
    ref_images, refs_used = resolve_reference_images(
        scene_number,
        ref_ctx,
        character_refs=payload.get("character_refs") or [],
        environment_refs=payload.get("environment_refs") or [],
    )

    layout = scene_grid_layout(payload.get("grid_size"))
    aspect_ratio = str(payload.get("aspect_ratio") or "16:9")
    style = payload.get("style")
    prompt_data = await build_sheet_prompt(
        script,
        scene_number,
        frames,
        ref_ctx,
        layout=layout,
        aspect_ratio=aspect_ratio,
        style=style,
        has_character_refs=any(r["type"] == "character" for r in refs_used),
        has_environment_refs=any(r["type"] == "environment" for r in refs_used),
        ai_manager=getattr(ai_service, "ai_manager", None),
    )

    result = await generate_storyboard_image_urls(
        prompt=prompt_data["sheet_prompt"],
        refs=ref_images,
        model=payload.get("model"),
        generation_profile=payload.get("generation_profile"),
        count=1,
        size=None,
        aspect_ratio=aspect_ratio,
        width=None,
        height=None,
        style=style or "realistic",
        style_preset_id=None,
        style_spec=None,
        seed=None,
        steps=None,
        cfg_scale=None,
        negative_prompt=None,
        strength=None,
        ai_service=ai_service,
    )
    urls = result.get("urls") if isinstance(result, dict) else None
    if not urls:
        raise RuntimeError("宫格分镜图生成失败：未返回图片")

    stored = await ai_service._persist_generated_image(
        image_data=str(urls[0]),
        ip_name=f"script-{script_id}",
        category="scene-grid",
        prefix="ai-generated/scene-grid",
        metadata={
            "task_id": task_id,
            "script_id": script_id,
            "scene_number": scene_number,
            "kind": "scene_grid_sheet",
        },
        require_upload=False,
    )
    image_url = stored.get("oss_url") or stored.get("relative_path") or str(urls[0])

    durations = cell_durations(frames, layout.panel_count)
    cells = [
        {**cell, "duration": durations[index]}
        for index, cell in enumerate(prompt_data["cells"][: layout.panel_count])
    ]
    save_scene_grid(
        db,
        script_id=script_id,
        scene_number=scene_number,
        grid_payload={
            "scene_number": scene_number,
            "status": "ready",
            "sheet_prompt": prompt_data["sheet_prompt"],
            "prompt_source": prompt_data["prompt_source"],
            "cells": cells,
            "panel_count": layout.panel_count,
            "rows": layout.rows,
            "columns": layout.columns,
            "aspect_ratio": aspect_ratio,
            "image_url": image_url,
            "refs_used": refs_used,
            "model": result.get("model"),
            "provider": result.get("provider"),
            "generated_at": utc_now(),
        },
    )
