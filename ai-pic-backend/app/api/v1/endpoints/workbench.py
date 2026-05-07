from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.workbench import WorkbenchSummary
from app.services.workbench_service import WorkbenchService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/summary", response_model=WorkbenchSummary)
def get_workbench_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return WorkbenchService(db).summary_for_user(current_user.id)
