"""Storyboard image generation task processor."""

import copy as _copy
from typing import Any, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.repositories.storyboard_media_repository import (
    get_script_by_id,
    get_task_by_id,
    save_storyboard_image_frames,
)
from app.services.ai_service import ai_service
from app.services.storyboard.candidate_lineage import record_canvas_candidate_lineage

from .image_task_frame_generation import generate_frame_image
from .image_task_prompt_runtime import resolve_dimensions
from .image_task_refs import load_image_ref_context

logger = get_logger("storyboard_image_task")


def _task_is_cancelled(db, task) -> bool:
    if task is None:
        return False
    db.refresh(task)
    return task.status.value == "cancelled"


def _process_storyboard_image_task(
    task_id: int,
    script_id: int,
    frame_indexes: list[int] | None,
    *,
    prompt_override: str | None = None,
    model: str | None = None,
    generation_profile: str | None = None,
    size: str | None = None,
    width: int | None = None,
    height: int | None = None,
    style: str = "realistic",
    style_preset_id: str | None = None,
    style_spec: dict[str, Any] | None = None,
    aspect_ratio: str | None = None,
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
    negative_prompt: str | None = None,
    strength: float | None = None,
    reference_images: Optional[List[str]] = None,
    labeled_references: Optional[List[dict[str, Any]]] = None,
    count: int = 1,
    keyframe_mode: str = "single",
    start_enabled: bool = True,
    end_enabled: bool = True,
    require_reference_images: bool = False,
    canvas_branch: dict[str, Any] | None = None,
):
    from app.core.database import SessionLocal
    from app.models.task import TaskStatus

    db = SessionLocal()
    try:
        task = get_task_by_id(db, task_id)
        if task:
            if _task_is_cancelled(db, task):
                logger.info(f"[SBIMG] task cancelled before start | task={task_id}")
                return
            task.status = TaskStatus.PROCESSING
            db.commit()

        script = get_script_by_id(db, script_id)
        if not script:
            raise RuntimeError("剧本不存在")
        sb = (
            (script.extra_metadata or {}).get("storyboard")
            if script.extra_metadata
            else None
        )
        if not sb or not sb.get("frames"):
            raise RuntimeError("未找到分镜数据")

        frames_src = list((sb or {}).get("frames") or [])
        frames = [
            _copy.deepcopy(fr) if isinstance(fr, dict) else fr for fr in frames_src
        ]
        target_indexes = frame_indexes or list(range(len(frames)))

        logger.info(
            f"[SBIMG] task start | script={script_id} task={task_id} "
            f"total={len(frames)} targets={target_indexes} model={model}"
        )

        ctx = load_image_ref_context(db, script, script_id)
        w, h = resolve_dimensions(width, height, size)
        count_int = max(1, min(4, int(count) if count is not None else 1))

        from app.services.storyboard.dynamic_prompt import build_dynamic_prompt_bundles

        dynamic_prompt_bundles = build_dynamic_prompt_bundles(
            script,
            frames,
            target_indexes,
            ctx,
            style=style,
            style_spec=style_spec,
            prompt_override=prompt_override,
            ai_service=ai_service,
        )
        if _task_is_cancelled(db, task):
            logger.info(f"[SBIMG] task cancelled after prompt | task={task_id}")
            return

        resolved_style_spec_used: dict | None = None
        resolved_style_spec_resolution_used: Any = None
        generated_frame_indexes: list[int] = []

        for idx in target_indexes:
            if _task_is_cancelled(db, task):
                logger.info(
                    f"[SBIMG] task cancelled before frame | task={task_id} frame={idx}"
                )
                return
            if idx < 0 or idx >= len(frames):
                logger.warning(f"[SBIMG] frame index out of range: {idx}/{len(frames)}")
                continue
            result_meta = generate_frame_image(
                frames,
                idx,
                ctx,
                options={
                    "prompt_override": prompt_override,
                    "model": model,
                    "generation_profile": generation_profile,
                    "size": size,
                    "width": w,
                    "height": h,
                    "style": style,
                    "style_preset_id": style_preset_id,
                    "style_spec": style_spec,
                    "aspect_ratio": aspect_ratio,
                    "seed": seed,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "negative_prompt": negative_prompt,
                    "strength": strength,
                    "reference_images": reference_images,
                    "labeled_references": labeled_references,
                    "count": count_int,
                    "keyframe_mode": keyframe_mode,
                    "start_enabled": start_enabled,
                    "end_enabled": end_enabled,
                    "require_reference_images": require_reference_images,
                    "script_id": script_id,
                    "dynamic_prompt_bundle": dynamic_prompt_bundles.get(idx),
                },
                prompt_manager=prompt_manager,
                ai_service=ai_service,
            )
            record_canvas_candidate_lineage(
                frames[idx],
                result_meta.get("generated_urls") or [],
                canvas_branch,
                task_id=task_id,
            )
            if result_meta.get("generated_urls"):
                generated_frame_indexes.append(idx)
            if resolved_style_spec_used is None and result_meta.get("style_spec"):
                resolved_style_spec_used = result_meta["style_spec"]
                resolved_style_spec_resolution_used = result_meta.get(
                    "style_spec_resolution"
                )

        if _task_is_cancelled(db, task):
            logger.info(f"[SBIMG] task cancelled before save | task={task_id}")
            return
        if target_indexes and not generated_frame_indexes:
            raise RuntimeError(
                "storyboard image generation produced no persisted images "
                f"for frames: {target_indexes}"
            )
        save_storyboard_image_frames(
            db,
            script_id=script_id,
            storyboard=sb,
            frames=frames,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            resolved_style_spec=resolved_style_spec_used,
            resolved_resolution=resolved_style_spec_resolution_used,
        )
        if task:
            if _task_is_cancelled(db, task):
                return
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as e:
        task = get_task_by_id(db, task_id)
        if task:
            if _task_is_cancelled(db, task):
                return
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()
