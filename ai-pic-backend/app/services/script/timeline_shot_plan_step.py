from __future__ import annotations

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineShotPlanRequest
from app.services.timeline_shot_plan_service import TimelineShotPlanService
from sqlalchemy.orm import Session


async def generate_timeline_shot_plan_from_current_version(
    db: Session,
    timeline: Timeline,
    *,
    user_id: int | None,
) -> Timeline:
    return await TimelineShotPlanService(db).generate_shot_plan_for_timeline(
        timeline,
        TimelineShotPlanRequest(expected_version=timeline.version),
        user_id=user_id,
    )
