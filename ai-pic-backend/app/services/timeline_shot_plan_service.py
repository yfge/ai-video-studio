from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline import TimelineResponse, TimelineShotPlanRequest
from app.services.ai.structured_output import parse_json_dict
from app.services.ai_service import ai_service
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_responses import timeline_response
from app.services.timeline_revision_service import TimelineRevisionService
from app.services.timeline_shot_plan_payloads import (
    SHOT_PLAN_SCHEMA,
    TimelineShotPlan,
    apply_timeline_shot_plan,
    build_timeline_shot_plan_prompt,
    clips_for_track,
    validate_timeline_shot_plan_matches,
)
from app.services.timeline_spec_validation import validate_timeline_spec
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session


class TimelineShotPlanService:
    def __init__(self, db: Session, *, ai_manager: Any | None = None):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.revisions = TimelineRevisionService(db)
        self.clip_lineage = TimelineClipAssetLineageService(db)
        self.ai_manager = (
            ai_manager if ai_manager is not None else ai_service.ai_manager
        )

    async def generate_shot_plan(
        self,
        timeline_id: int,
        payload: TimelineShotPlanRequest,
        current_user: User,
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        updated = await self.generate_shot_plan_for_timeline(
            timeline,
            payload,
            user_id=current_user.id,
        )
        return timeline_response(updated)

    async def generate_shot_plan_for_timeline(
        self,
        timeline: Timeline,
        payload: TimelineShotPlanRequest,
        *,
        user_id: int | None,
    ) -> Timeline:
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )
        if self.ai_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="timeline shot plan AI manager unavailable",
            )

        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        video_clips = clips_for_track(spec, "video")
        if not video_clips:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline video clips missing",
            )

        plan = await self._generate_plan(spec, payload)
        updated_spec = apply_timeline_shot_plan(
            spec,
            plan,
            provider=plan["provider"],
            model=plan["model"],
            style=payload.style,
        )

        next_version = timeline.version + 1
        updated_spec["version"] = next_version
        updated_spec["timeline_id"] = timeline.id
        validate_timeline_spec(
            updated_spec,
            episode_id=timeline.episode_id,
            script_id=timeline.script_id,
            timeline_id=timeline.id,
            expected_version=next_version,
            require_timeline_id=True,
        )

        self.revisions.ensure_revision(
            timeline,
            reason="pre_shot_plan_snapshot",
            user_id=user_id,
        )
        timeline.spec = updated_spec
        timeline.version = next_version
        timeline.updated_by = user_id
        timeline.rollback_of_version = None
        timeline.rollback_target_version = None
        timeline.rolled_back_at = None
        timeline.rolled_back_by = None
        timeline.spec = self.revisions.spec_with_identity(timeline)
        self.clip_lineage.sync_timeline_assets(timeline, user_id=user_id)
        self.revisions.ensure_revision(
            timeline,
            reason="shot_plan_generated",
            user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(timeline)
        return timeline

    async def _generate_plan(
        self,
        spec: dict[str, Any],
        payload: TimelineShotPlanRequest,
    ) -> dict[str, Any]:
        response = await self.ai_manager.generate_text(
            prompt=build_timeline_shot_plan_prompt(spec, style=payload.style),
            model=payload.model,
            prefer_provider=payload.prefer_provider,
            temperature=payload.temperature,
            max_tokens=2800,
            json_schema={"name": "timeline_shot_plan", "schema": SHOT_PLAN_SCHEMA},
            system_prompt="You are a strict JSON writer. Output JSON only.",
            stream=False,
        )
        if not getattr(response, "success", False):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"timeline shot plan generation failed: {getattr(response, 'error', None)}",
            )

        raw = parse_json_dict(getattr(response, "data", None))
        try:
            parsed = TimelineShotPlan.model_validate(raw)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "timeline shot plan JSON invalid",
                    "errors": exc.errors(),
                },
            ) from exc

        normalized = parsed.model_dump()
        mismatch = validate_timeline_shot_plan_matches(normalized, spec)
        if mismatch:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=mismatch,
            )
        return {
            "shots": normalized["shots"],
            "provider": getattr(response, "provider", None),
            "model": getattr(response, "model", None) or payload.model,
            "usage": getattr(response, "usage", None),
        }

    def _get_timeline_or_404(self, timeline_id: int, current_user: User) -> Timeline:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=self._story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        return timeline

    @staticmethod
    def _story_owner_filter(current_user: User) -> int | None:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id
