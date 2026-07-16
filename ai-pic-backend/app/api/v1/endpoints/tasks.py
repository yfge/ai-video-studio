import json
import logging

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import TASK_STATUS_TRANSITIONS, Task, TaskStatus, TaskType
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskList, TaskResponse, TaskUpdate
from app.services.task_result_context import build_task_result_context
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_task(task: Task) -> TaskResponse:
    """将ORM任务对象序列化为响应模型，解析parameters为dict"""
    params = None
    if task.parameters:
        try:
            params = json.loads(task.parameters)
        except Exception:
            params = None

    progress_detail = task.description or None
    if task.status in {TaskStatus.FAILED, TaskStatus.CANCELLED} and task.error_message:
        progress_detail = task.error_message

    return TaskResponse(
        id=task.id,
        business_id=getattr(task, "business_id", None),
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        prompt=task.prompt,
        parameters=params,
        status=task.status,
        result_file_path=task.result_file_path,
        error_message=task.error_message,
        user_id=task.user_id,
        target_business_id=getattr(task, "target_business_id", None),
        progress_detail=progress_detail,
        created_at=task.created_at,
        updated_at=task.updated_at,
        result_context=build_task_result_context(
            task_id=task.id,
            parameters=params,
            result_file_path=task.result_file_path,
        ),
    )


def _task_or_404(db: Session, task_id: int, user_id: int) -> Task:
    task = TaskRepository(db).get_user_task(task_id=task_id, user_id=user_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新任务"""
    # 将参数转换为JSON字符串
    parameters_json = None
    if task_data.parameters:
        parameters_json = json.dumps(task_data.parameters)

    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        prompt=task_data.prompt,
        parameters=parameters_json,
        user_id=current_user.id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return _serialize_task(db_task)


@router.get("/", response_model=TaskList)
def get_tasks(
    skip: int = 0,
    limit: int = 20,
    status_filter: TaskStatus = None,
    task_type: TaskType = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户的任务列表"""
    tasks, total = TaskRepository(db).list_for_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        task_type=task_type,
    )
    return TaskList(
        tasks=[_serialize_task(t) for t in tasks],
        total=total,
        page=skip // limit + 1,
        size=limit,
    )


@router.get("", response_model=TaskList, include_in_schema=False)
def get_tasks_no_slash(
    skip: int = 0,
    limit: int = 20,
    status_filter: TaskStatus = None,
    task_type: TaskType = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    兼容无尾斜杠的 /api/v1/tasks 请求，避免 FastAPI 返回 307 重定向。

    内部直接复用 get_tasks 的分页与过滤逻辑。
    """
    return get_tasks(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        task_type=task_type,
        db=db,
        current_user=current_user,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取特定任务信息"""
    return _serialize_task(_task_or_404(db, task_id, current_user.id))


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新任务信息"""
    task = _task_or_404(db, task_id, current_user.id)
    # 更新任务信息
    update_data = task_data.model_dump(exclude_unset=True)

    # Validate status transitions
    if "status" in update_data:
        new_status = update_data["status"]
        allowed = TASK_STATUS_TRANSITIONS.get(task.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"不允许从 {task.status.value} 转换到 {new_status.value}，"
                    f"允许的目标状态: {[s.value for s in allowed] or '无'}"
                ),
            )

    # 如果更新参数，需要转换为JSON字符串
    if "parameters" in update_data:
        update_data["parameters"] = json.dumps(update_data["parameters"])

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    # Keep response consistent with other endpoints (parameters as dict)
    return _serialize_task(task)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除任务"""
    task = _task_or_404(db, task_id, current_user.id)
    task.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "任务已删除"}


def _dispatch_celery_task(task: Task, user_id: int) -> bool:
    """Dispatch a Task to the matching Celery worker. Returns True on success."""
    params = {}
    if task.parameters:
        try:
            params = json.loads(task.parameters)
        except Exception:
            params = {}

    from app.services.task_worker import (
        episode_generate_task,
        script_audio_timeline_generate_task,
        script_dialogue_audio_generate_task,
        script_generate_task,
        script_regenerate_task,
        story_generate_task,
        story_novel_generate_task,
        storyboard_generate_task,
        timeline_pipeline_generate_task,
    )
    from app.services.task_worker_assets import (
        environment_image_generate_task,
        environment_image_variant_task,
        virtual_ip_image_generate_task,
        virtual_ip_image_variant_task,
    )
    from app.services.task_worker_storyboard_media import (
        storyboard_image_generate_task,
        storyboard_video_generate_task,
    )
    from app.services.task_worker_timeline_rework import (
        timeline_clip_rework_video_generate_task,
    )

    if (
        task.task_type == TaskType.VIDEO_GENERATION
        and isinstance(params, dict)
        and params.get("timeline_id")
        and params.get("clip_id")
    ):
        timeline_clip_rework_video_generate_task.delay(task.id, params, user_id)
        return True

    dispatch_map = {
        TaskType.STORY_GENERATION: story_generate_task,
        TaskType.TEXT_GENERATION: story_novel_generate_task,
        TaskType.EPISODE_GENERATION: episode_generate_task,
        TaskType.SCRIPT_GENERATION: script_generate_task,
        TaskType.SCRIPT_REVIEW: script_regenerate_task,
        TaskType.DIALOGUE_AUDIO_GENERATION: script_dialogue_audio_generate_task,
        TaskType.TIMELINE_GENERATION: script_audio_timeline_generate_task,
        TaskType.STORYBOARD_GENERATION: storyboard_generate_task,
        TaskType.TIMELINE_PIPELINE: timeline_pipeline_generate_task,
        TaskType.VIRTUAL_IP_IMAGE_GENERATION: virtual_ip_image_generate_task,
        TaskType.VIRTUAL_IP_IMAGE_VARIANT_GENERATION: virtual_ip_image_variant_task,
        TaskType.ENVIRONMENT_IMAGE_GENERATION: environment_image_generate_task,
        TaskType.ENVIRONMENT_IMAGE_VARIANT_GENERATION: environment_image_variant_task,
        TaskType.STORYBOARD_IMAGE_GENERATION: storyboard_image_generate_task,
        TaskType.VIDEO_GENERATION: storyboard_video_generate_task,
    }

    celery_task = dispatch_map.get(task.task_type)
    if celery_task is None:
        return False

    celery_task.delay(task.id, params, user_id)
    return True


@router.post("/{task_id}/start")
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """开始执行任务"""
    task = _task_or_404(db, task_id, current_user.id)
    if task.status not in (TaskStatus.PENDING, TaskStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({task.status.value})不允许开始执行",
        )

    dispatched = _dispatch_celery_task(task, current_user.id)
    if not dispatched:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务类型 {task.task_type.value} 暂不支持手动启动",
        )

    task.status = TaskStatus.PROCESSING
    task.error_message = None
    db.commit()
    logger.info("Task %s dispatched to Celery (type=%s)", task_id, task.task_type.value)

    return {"message": "任务已开始执行", "task_id": task_id}
