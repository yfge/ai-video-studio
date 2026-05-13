"""Storyboard media generation endpoints.

Handles image and video generation for storyboard frames.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.storyboard_media_repository import resolve_storyboard_aspect_ratio
from app.schemas.style import StyleSpec
from app.services.task_worker import (
    storyboard_image_generate_task,
    storyboard_video_generate_task,
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .utils import get_script_with_auth

router = APIRouter()
logger = get_logger()


class LabeledReference(BaseModel):
    """Reference image with metadata."""

    url: str
    label: Optional[str] = None
    type: Optional[str] = None  # character, environment, primary, other


class StoryboardImageRequest(BaseModel):
    """Request schema for storyboard image generation."""

    frames: Optional[List[int]] = Field(
        None, description="Frame indexes to generate images for"
    )
    model: Optional[str] = Field(None, description="Image model (e.g., keling:v1.5)")
    generation_profile: Optional[str] = None
    prompt: Optional[str] = Field(None, description="Custom prompt override")
    size: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    style: Optional[str] = None
    style_preset_id: Optional[int] = None
    style_spec: Optional[StyleSpec] = None
    reference_images: Optional[List[str]] = None
    labeled_references: Optional[List[LabeledReference]] = None
    seed: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    negative_prompt: Optional[str] = None
    strength: Optional[float] = None
    count: Optional[int] = 1
    keyframe_mode: Optional[str] = Field(
        None, description="Keyframe generation mode: start, end, both"
    )
    start_enabled: Optional[bool] = True
    end_enabled: Optional[bool] = True
    require_reference_images: Optional[bool] = Field(
        False,
        description="Fail image generation when a target frame has no reference images",
    )


class StoryboardVideoRequest(BaseModel):
    """Request schema for storyboard video generation."""

    frames: Optional[List[int]] = Field(
        None, description="Frame indexes to generate video for"
    )
    selections: Optional[List[Dict[str, Any]]] = Field(
        None, description="Frame selection specifications"
    )
    prompt: Optional[str] = None
    model: Optional[str] = Field(None, description="Video model (e.g., jimeng, keling)")
    duration: Optional[float] = None
    fps: Optional[int] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    watermark: Optional[bool] = None
    seed: Optional[int] = None
    camera_fixed: Optional[bool] = None
    camera_control: Optional[Dict[str, Any]] = None
    service_tier: Optional[str] = None
    execution_expires_after: Optional[int] = None
    return_last_frame: Optional[bool] = None
    use_end_frame: Optional[bool] = None


def _build_storyboard_image_payload(db, script, script_id: int, request):
    aspect_ratio = resolve_storyboard_aspect_ratio(
        db, script=script, requested=request.aspect_ratio
    )
    return {
        "script_id": script_id,
        "frame_indexes": request.frames,
        "frames": request.frames,
        "prompt_override": request.prompt,
        "prompt": request.prompt,
        "model": request.model,
        "generation_profile": request.generation_profile,
        "size": request.size,
        "width": request.width,
        "height": request.height,
        "aspect_ratio": aspect_ratio,
        "style": request.style,
        "style_preset_id": request.style_preset_id,
        "style_spec": request.style_spec.dict() if request.style_spec else None,
        "reference_images": request.reference_images,
        "labeled_references": (
            [r.dict() for r in request.labeled_references]
            if request.labeled_references
            else None
        ),
        "seed": request.seed,
        "steps": request.steps,
        "cfg_scale": request.cfg_scale,
        "negative_prompt": request.negative_prompt,
        "strength": request.strength,
        "count": request.count,
        "keyframe_mode": request.keyframe_mode,
        "start_enabled": request.start_enabled,
        "end_enabled": request.end_enabled,
        "require_reference_images": request.require_reference_images,
    }


def _build_storyboard_video_payload(db, script, script_id: int, request):
    ratio = resolve_storyboard_aspect_ratio(
        db, script=script, requested=request.ratio
    )
    return {
        "script_id": script_id,
        "frame_indexes": request.frames,
        "frames": request.frames,
        "selections": request.selections,
        "prompt": request.prompt,
        "model": request.model,
        "duration": request.duration,
        "fps": request.fps,
        "resolution": request.resolution,
        "ratio": ratio,
        "watermark": request.watermark,
        "seed": request.seed,
        "camera_fixed": request.camera_fixed,
        "camera_control": request.camera_control,
        "service_tier": request.service_tier,
        "execution_expires_after": request.execution_expires_after,
        "return_last_frame": request.return_last_frame,
        "use_end_frame": request.use_end_frame,
    }


@router.post("/{script_id}/storyboard/generate-images")
async def generate_storyboard_images(
    script_id: int,
    request: StoryboardImageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate AI images for storyboard frames.

    Queues background task and returns task ID for status polling.
    Supports keyframe generation (start, end, or both frames).
    """
    script = get_script_with_auth(db, script_id, current_user)
    payload = _build_storyboard_image_payload(db, script, script_id, request)

    # Create task record
    t = Task(
        title=f"分镜图生成 - 剧本{script_id}",
        description="异步生成分镜图像",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    # Queue background task
    storyboard_image_generate_task.delay(t.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


@router.post("/{script_id}/storyboard/generate-video")
async def generate_storyboard_video(
    script_id: int,
    request: StoryboardVideoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate video from storyboard frames.

    Queues background task and returns task ID for status polling.
    Supports multiple video models (jimeng, keling, etc.).
    """
    script = get_script_with_auth(db, script_id, current_user)
    payload = _build_storyboard_video_payload(db, script, script_id, request)

    # Create task record
    t = Task(
        title=f"分镜视频生成 - 剧本{script_id}",
        description="异步生成分镜视频",
        task_type=TaskType.VIDEO_GENERATION,
        prompt=f"Storyboard video generation for script {script_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    # Queue background task
    storyboard_video_generate_task.delay(t.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": t.id, "status": t.status}}
