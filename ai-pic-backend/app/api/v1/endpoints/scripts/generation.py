"""
Script generation endpoints.

Provides API routes for AI-powered script generation including
synchronous generation, async generation, and prompt preview.
"""

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.script import ScriptResponse
from app.services.script import ScriptGenerator, get_script_generator
from app.services.task_worker import script_generate_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def get_generator(db: Session = Depends(get_db)) -> ScriptGenerator:
    """Dependency to get ScriptGenerator instance."""
    return get_script_generator(db)


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    generator: ScriptGenerator = Depends(get_generator),
):
    """
    使用AI生成剧本（同步）

    生成指定剧集的剧本，返回生成结果。
    此接口为同步调用，可能需要较长时间。
    """
    script = await generator.generate_script(
        episode_id=request.episode_id,
        user=current_user,
        format_type=request.format_type,
        language=request.language,
        model=request.model,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
        quality_threshold=request.quality_threshold,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        temperature=request.temperature or 0.7,
    )
    return ScriptResponse.from_orm(script)


@router.post("/generate-async")
async def generate_script_async(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    使用AI生成剧本（异步）

    创建异步任务生成剧本，立即返回任务ID。
    可通过任务接口查询生成进度和结果。
    """
    task = Task(
        title=f"生成剧本 - 剧集{request.episode_id}",
        description="异步剧本生成",
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=f"Script for episode {request.episode_id}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 交给 Celery worker 处理
    script_generate_task.delay(task.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.post("/prompt/preview")
async def preview_script_prompt(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    generator: ScriptGenerator = Depends(get_generator),
):
    """
    预览剧本生成提示词

    返回将要发送给AI的提示词内容，用于调试和优化。
    """
    prompt = generator.preview_prompt(
        episode_id=request.episode_id,
        user=current_user,
        format_type=request.format_type,
        language=request.language,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
        quality_threshold=request.quality_threshold,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
    )
    return {"success": True, "data": {"prompt": prompt}}
