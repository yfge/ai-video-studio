from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.task import TaskStatus, TaskType

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType
    prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskList(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    size: int 