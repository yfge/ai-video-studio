"""Storyboard media generation endpoints.

Handles image and video generation for storyboard frames.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Story
from app.models.task import Task, TaskType
from app.models.user import User
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
    prompt: Optional[str] = Field(None, description="Custom prompt override")
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
    keyframe_mode: Optional[str] = Field(
        None, description="Keyframe generation mode: start, end, both"
    )
    start_enabled: Optional[bool] = True
    end_enabled: Optional[bool] = True


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

    # Resolve aspect ratio from request or story defaults
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = None
    if episode:
        story = db.query(Story).filter(Story.id == episode.story_id).first()

    aspect_ratio = request.aspect_ratio
    if not aspect_ratio:
        # Try episode, then story defaults
        if episode and episode.extra_metadata:
            aspect_ratio = episode.extra_metadata.get("aspect_ratio")
        if not aspect_ratio and story and story.extra_metadata:
            aspect_ratio = story.extra_metadata.get("aspect_ratio")

    payload = {
        "script_id": script_id,
        "frame_indexes": request.frames,
        "frames": request.frames,
        "prompt_override": request.prompt,
        "prompt": request.prompt,
        "model": request.model,
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
        "keyframe_mode": request.keyframe_mode,
        "start_enabled": request.start_enabled,
        "end_enabled": request.end_enabled,
    }

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

    # Resolve aspect ratio
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = None
    if episode:
        story = db.query(Story).filter(Story.id == episode.story_id).first()

    ratio = request.ratio
    if not ratio:
        if episode and episode.extra_metadata:
            ratio = episode.extra_metadata.get("aspect_ratio")
        if not ratio and story and story.extra_metadata:
            ratio = story.extra_metadata.get("aspect_ratio")

    payload = {
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
