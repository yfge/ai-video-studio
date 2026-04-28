"""Storyboard generation endpoints.

Handles synchronous and asynchronous storyboard frame generation.
Uses the new React validation pipeline when use_new_pipeline=True.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script
from app.models.task import Task, TaskType
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.storyboard.pipeline import StoryboardPipeline
from app.services.task_worker import storyboard_generate_task
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .utils import get_script_with_auth

router = APIRouter()
logger = get_logger()


class StoryboardUpdateRequest(BaseModel):
    """Request schema for storyboard update."""

    frames: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of storyboard frames",
    )


@router.post("/{script_id}/storyboard/generate")
async def generate_storyboard(
    script_id: int,
    model: str | None = None,
    temperature: float = Query(0.7, ge=0.0, le=1.5, description="创造性温度"),
    frames_per_scene: int = Query(7, ge=1, le=10, description="每场景建议分镜数"),
    max_frames: int | None = Query(None, ge=1, le=500, description="最大分镜帧数上限"),
    scene_numbers: str | None = Query(
        None, description="逗号分隔的场景编号列表，如 1,3,4"
    ),
    use_plan: bool = Query(True, description="是否先使用分镜规划，再逐场景生成"),
    use_new_pipeline: bool = Query(
        False, description="是否使用新的React验证管线（实验性）"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate storyboard frames synchronously.

    Supports two modes:
    - Legacy mode: Uses ai_service.generate_storyboard directly
    - New pipeline mode: Uses StoryboardPipeline with React validation

    Args:
        script_id: Target script ID
        model: AI model in format "provider:model_id" or just "model_id"
        temperature: Creativity level (0.0-1.5)
        frames_per_scene: Target frames per scene (1-10)
        max_frames: Maximum total frames cap
        scene_numbers: Comma-separated scene numbers to generate for
        use_plan: Whether to use planning phase before generation
        use_new_pipeline: Use new React validation pipeline (experimental)
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    # Parse selected scenes
    selected_scenes: list[int] | None = None
    if scene_numbers:
        try:
            selected_scenes = [
                int(x.strip()) for x in scene_numbers.split(",") if x.strip()
            ]
        except Exception:
            raise HTTPException(status_code=400, detail="scene_numbers 格式不正确")

    # Parse provider and model
    prefer_provider = "openai"
    model_id = model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    # Use new React validation pipeline (experimental)
    if use_new_pipeline:
        return await _generate_with_new_pipeline(
            db=db,
            script=script,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            model_id=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            max_frames=max_frames,
            use_plan=use_plan,
        )

    # Legacy generation - delegate to storyboard.legacy_generate
    from app.api.v1.endpoints.storyboard.legacy_generate import (
        generate_storyboard_logic,
    )

    # Parse selected scenes (same logic as above for new pipeline)
    selected_scenes_parsed: list[int] | None = None
    if scene_numbers:
        try:
            selected_scenes_parsed = [
                int(x.strip()) for x in scene_numbers.split(",") if x.strip()
            ]
        except Exception:
            raise HTTPException(status_code=400, detail="scene_numbers 格式不正确")

    return await generate_storyboard_logic(
        script,
        db,
        model=model,
        temperature=temperature,
        frames_per_scene=frames_per_scene,
        max_frames=max_frames,
        selected_scenes=selected_scenes_parsed,
        use_plan=use_plan,
    )


async def _generate_with_new_pipeline(
    db: Session,
    script: Script,
    frames_per_scene: int,
    selected_scenes: Optional[List[int]],
    model_id: Optional[str],
    prefer_provider: str,
    temperature: float,
    max_frames: Optional[int],
    use_plan: bool,
) -> dict:
    """Generate storyboard using new React validation pipeline."""
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    pipeline = StoryboardPipeline(db, ai_service=ai_service)

    try:
        result = await pipeline.generate(
            script=script,
            episode=episode,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            max_frames=max_frames,
            use_langgraph=use_plan,
        )
    except Exception as exc:
        logger.error(f"New pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=f"管线执行失败: {exc}")

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error") or "分镜生成失败",
        )

    frames = result.get("frames", [])
    if not frames:
        raise HTTPException(status_code=500, detail="分镜生成失败：无帧返回")

    # Persist results
    sb_meta = {
        "version": script.storyboard_version,
        "updated_at": (
            script.storyboard_updated_at.isoformat()
            if script.storyboard_updated_at
            else None
        ),
        "generation_source": "new_pipeline",
        "generation_method": result.get("phase", "unknown"),
        "provider": result.get("provider_used"),
        "scene_scope": selected_scenes,
        "validation_results": result.get("validation_results"),
        "reasoning_trace": result.get("reasoning_trace"),
    }
    sb = {"frames": frames, "meta": sb_meta}
    extra = dict(script.extra_metadata or {})
    extra["storyboard"] = sb
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.now(timezone.utc)
    script.storyboard_version = (script.storyboard_version or 0) + 1
    db.commit()
    db.refresh(script)

    return {"success": True, "data": sb, "pipeline_result": result}


@router.post("/{script_id}/storyboard/generate-async")
async def generate_storyboard_async(
    script_id: int,
    model: str | None = None,
    temperature: float = Query(0.7, ge=0.0, le=1.5),
    frames_per_scene: int = Query(7, ge=1, le=10),
    max_frames: int | None = Query(None, ge=1, le=500),
    scene_numbers: str | None = Query(None),
    use_plan: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue storyboard generation as background task.

    Returns immediately with task ID for status polling.
    """
    get_script_with_auth(db, script_id, current_user)

    task_payload = {
        "script_id": script_id,
        "model": model,
        "temperature": temperature,
        "frames_per_scene": frames_per_scene,
        "max_frames": max_frames,
        "scene_numbers": scene_numbers,
        "use_plan": use_plan,
    }

    # Create task record
    t = Task(
        title=f"生成分镜 - 剧本{script_id}",
        description="异步分镜结构生成",
        task_type=TaskType.STORYBOARD_GENERATION,
        prompt=f"Storyboard generation for script {script_id}",
        parameters=json.dumps(task_payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    # Queue background task
    storyboard_generate_task.delay(
        t.id,
        task_payload,
        current_user.id,
    )

    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


@router.post("/{script_id}/storyboard/update")
async def update_storyboard(
    script_id: int,
    request: StoryboardUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Save edited storyboard frames to database.

    Performs wholesale update of all frames with version tracking.
    """
    from uuid import uuid4

    script = get_script_with_auth(db, script_id, current_user)

    frames = request.frames
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Validate and serialize frames
    serialized_frames = []
    for i, frame in enumerate(frames, start=1):
        # Ensure required fields
        serialized = {
            "frame_id": frame.get("frame_id") or str(uuid4()),
            "frame_number": frame.get("frame_number", i),
            "scene_number": frame.get("scene_number", 1),
            "description": frame.get("description", ""),
            "ai_prompt": frame.get("ai_prompt", frame.get("description", "")),
            "shot_type": frame.get("shot_type"),
            "camera_movement": frame.get("camera_movement"),
            "composition": frame.get("composition"),
            "duration_seconds": frame.get("duration_seconds", 3),
            "image_url": frame.get("image_url"),
            "video_url": frame.get("video_url"),
            "updated_at": now_iso,
        }

        # Preserve optional fields
        for key in ["start_ms", "end_ms", "reference_images", "characters"]:
            if key in frame:
                serialized[key] = frame[key]

        serialized_frames.append(serialized)

    # Update script metadata
    new_version = (script.storyboard_version or 0) + 1
    sb_meta = {
        "version": new_version,
        "updated_at": now_iso,
        "generation_source": "manual_edit",
        "generation_method": "user_update",
    }
    sb = {"frames": serialized_frames, "meta": sb_meta}

    extra = dict(script.extra_metadata or {})
    extra["storyboard"] = sb
    script.extra_metadata = extra
    script.storyboard_version = new_version
    script.storyboard_updated_at = now
    db.commit()

    return {
        "success": True,
        "data": {
            "message": "分镜已保存",
            "version": new_version,
            "frame_count": len(serialized_frames),
        },
    }
