from __future__ import annotations

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineShotPlanRequest
from app.services.timeline_shot_plan_models import TimelineShotPlan
from app.services.timeline_shot_plan_payloads import (
    clips_for_track,
    validate_timeline_shot_plan_matches,
)
from app.services.timeline_shot_plan_service import TimelineShotPlanService
from pydantic import ValidationError
from sqlalchemy.orm import Session


async def generate_timeline_shot_plan_from_current_version(
    db: Session,
    timeline: Timeline,
    *,
    user_id: int | None,
) -> Timeline:
    if timeline_has_complete_shot_plan(timeline):
        return timeline
    return await TimelineShotPlanService(db).generate_shot_plan_for_timeline(
        timeline,
        TimelineShotPlanRequest(expected_version=timeline.version),
        user_id=user_id,
    )


def timeline_has_complete_shot_plan(timeline: Timeline) -> bool:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    video_clips = clips_for_track(spec, "video")
    if not video_clips:
        return False

    shots = []
    for clip in video_clips:
        source_refs = clip.get("source_refs")
        source_refs = source_refs if isinstance(source_refs, dict) else {}
        shot = source_refs.get("timeline_shot_plan")
        if not isinstance(shot, dict):
            return False
        shots.append(shot)

    try:
        normalized = TimelineShotPlan.model_validate({"shots": shots}).model_dump()
    except ValidationError:
        return False
    return validate_timeline_shot_plan_matches(normalized, spec) is None
