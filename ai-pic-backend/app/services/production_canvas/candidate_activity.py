from app.models.user import User
from sqlalchemy.orm import Session

from .collaboration import record_canvas_activity


def record_canvas_candidate_activity(
    db: Session,
    user: User,
    run_id: str,
    action: str,
    candidate_id: int,
    detail: str | None = None,
) -> None:
    record_canvas_activity(
        db,
        user,
        run_id,
        action,
        target_type="candidate",
        target_id=str(candidate_id),
        detail=detail,
    )
