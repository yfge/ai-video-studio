from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.services.task_control_service import TaskControlService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/tasks/{task_id}/cancel",
    summary="Cancel a pending/processing task (best-effort)",
)
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskControlService(db)
    task = service.cancel_task(task_id, current_user)
    return {
        "success": True,
        "data": {
            "task_id": task.id,
            "status": (
                task.status.value
                if hasattr(task.status, "value")
                else str(task.status)
            ),
        },
    }
