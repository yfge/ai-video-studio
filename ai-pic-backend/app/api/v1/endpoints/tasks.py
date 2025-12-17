import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskType
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskList
from app.core.middleware import get_current_active_user

router = APIRouter()


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _serialize_task(task: Task) -> TaskResponse:
    """将ORM任务对象序列化为响应模型，解析parameters为dict"""
    params = None
    if task.parameters:
        try:
            params = json.loads(task.parameters)
        except Exception:
            params = None

    progress_detail = task.description or None
    if task.status == TaskStatus.FAILED and task.error_message:
        progress_detail = task.error_message

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        prompt=task.prompt,
        parameters=params,
        status=task.status,
        result_file_path=task.result_file_path,
        error_message=task.error_message,
        user_id=task.user_id,
        progress_detail=progress_detail,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
        user_id=current_user.id
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
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的任务列表"""
    query = _not_deleted(db.query(Task), Task).filter(Task.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    if task_type:
        query = query.filter(Task.task_type == task_type)
    
    total = query.count()
    tasks = query.order_by(Task.id.desc()).offset(skip).limit(limit).all()
    
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
    current_user: User = Depends(get_current_active_user)
):
    """获取特定任务信息"""
    task = (
        _not_deleted(db.query(Task), Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return _serialize_task(task)

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新任务信息"""
    task = (
        _not_deleted(db.query(Task), Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新任务信息
    update_data = task_data.model_dump(exclude_unset=True)
    
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
    current_user: User = Depends(get_current_active_user)
):
    """删除任务"""
    task = (
        _not_deleted(db.query(Task), Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()
    
    return {"message": "任务已删除"}

@router.post("/{task_id}/start")
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """开始执行任务"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务状态不允许开始执行"
        )
    
    # 更新任务状态为处理中
    task.status = TaskStatus.PROCESSING
    db.commit()
    
    # TODO: 这里应该启动异步任务处理
    # 例如：celery.delay(process_task, task.id)
    
    return {"message": "任务已开始执行", "task_id": task_id} 
