"""Scene grid storyboard endpoints: grid sheet + continuous video generation."""

import json

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.storyboard_media_repository import load_scene_grids
from app.schemas.storyboard_scene_grid import (
    SceneGridSheetRequest,
    SceneGridVideoRequest,
)
from app.services.task_worker_scene_grid import (
    scene_grid_sheet_generate_task,
    scene_grid_video_generate_task,
)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .utils import get_script_with_auth

router = APIRouter()
logger = get_logger()


@router.post("/{script_id}/storyboard/scene-grid/generate")
async def generate_scene_grid_sheet(
    script_id: int,
    request: SceneGridSheetRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate one scene's grid storyboard sheet (async, returns task id).

    Character/environment reference images can be selected explicitly; when
    omitted they are auto-resolved from scene bindings.
    """
    get_script_with_auth(db, script_id, current_user)
    payload = {
        "script_id": script_id,
        "scene_number": request.scene_number,
        "grid_size": request.grid_size,
        "model": request.model,
        "generation_profile": request.generation_profile,
        "style": request.style,
        "aspect_ratio": request.aspect_ratio,
        "character_refs": [
            ref.model_dump() for ref in (request.character_refs or [])
        ],
        "environment_refs": request.environment_refs or [],
    }
    task = Task(
        title=f"宫格分镜图生成 - 剧本{script_id} 场景{request.scene_number}",
        description="异步生成场景宫格分镜大图",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        prompt=f"Scene grid sheet for script {script_id} scene {request.scene_number}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    scene_grid_sheet_generate_task.delay(task.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.post("/{script_id}/storyboard/scene-grid/video")
async def generate_scene_grid_video(
    script_id: int,
    request: SceneGridVideoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a continuous multi-shot video from the scene grid sheet."""
    get_script_with_auth(db, script_id, current_user)
    payload = {
        "script_id": script_id,
        "scene_number": request.scene_number,
        "model": request.model,
        "duration": request.duration,
        "resolution": request.resolution,
        "ratio": request.ratio,
        "generate_audio": request.generate_audio,
        "prompt": request.prompt,
    }
    task = Task(
        title=f"宫格成片生成 - 剧本{script_id} 场景{request.scene_number}",
        description="异步从宫格分镜图生成连续成片",
        task_type=TaskType.VIDEO_GENERATION,
        prompt=f"Scene grid video for script {script_id} scene {request.scene_number}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    scene_grid_video_generate_task.delay(task.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.get("/{script_id}/storyboard/scene-grid")
async def list_scene_grids(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List generated scene grids (sheet + video) for a script."""
    get_script_with_auth(db, script_id, current_user)
    return {"success": True, "data": {"scene_grids": load_scene_grids(db, script_id)}}
