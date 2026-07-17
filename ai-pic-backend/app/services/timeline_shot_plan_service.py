from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline import TimelineResponse, TimelineShotPlanRequest
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_responses import timeline_response
from app.services.timeline_revision_service import TimelineRevisionService
from app.services.timeline_shot_plan_batching import (
    SHOT_PLAN_BATCH_SIZE,
    batched,
    invalid_batch_detail,
    last_attempt,
    merge_usage,
    plan_mismatch_errors,
    shot_plan_batch_max_tokens,
    spec_for_video_clip_ids,
)
from app.services.timeline_shot_plan_coercion import coerce_timeline_shot_plan_payload
from app.services.timeline_shot_plan_models import TimelineShotPlan
from app.services.timeline_shot_plan_payloads import (
    SHOT_PLAN_SCHEMA,
    apply_timeline_shot_plan,
    build_timeline_shot_plan_prompt,
    clips_for_track,
    validate_timeline_shot_plan_matches,
)
from app.services.timeline_spec_validation import validate_timeline_spec
from fastapi import HTTPException, status
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
        video_clips = clips_for_track(spec, "video")
        batches = batched(video_clips, SHOT_PLAN_BATCH_SIZE)
        merged_shots: list[dict[str, Any]] = []
        provider: str | None = None
        model: str | None = None
        usage: dict[str, Any] = {}

        for batch_index, batch in enumerate(batches, start=1):
            batch_result = await self._generate_plan_batch(
                spec,
                payload,
                batch,
                batch_index=batch_index,
                batch_count=len(batches),
            )
            merged_shots.extend(batch_result["shots"])
            provider = provider or batch_result.get("provider")
            model = model or batch_result.get("model")
            usage = merge_usage(usage, batch_result.get("usage"))

        normalized = {"shots": merged_shots}
        mismatch = validate_timeline_shot_plan_matches(normalized, spec)
        if mismatch:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=mismatch,
            )
        return {
            "shots": normalized["shots"],
            "provider": provider,
            "model": model or payload.model,
            "usage": usage,
        }

    async def _generate_plan_batch(
        self,
        spec: dict[str, Any],
        payload: TimelineShotPlanRequest,
        batch: list[dict[str, Any]],
        *,
        batch_index: int,
        batch_count: int,
    ) -> dict[str, Any]:
        clip_ids = [str(clip.get("clip_id")) for clip in batch]
        clip_id_set = set(clip_ids)
        max_tokens = shot_plan_batch_max_tokens(len(batch))
        batch_spec = spec_for_video_clip_ids(spec, clip_id_set)
        result = await generate_with_repair(
            ai_manager=self.ai_manager,
            base_prompt=build_timeline_shot_plan_prompt(
                spec,
                style=payload.style,
                clip_ids=clip_id_set,
            ),
            model=payload.model,
            prefer_provider=payload.prefer_provider,
            temperature=payload.temperature,
            schema_name="timeline_shot_plan",
            schema=SHOT_PLAN_SCHEMA,
            system_prompt="You are a strict JSON writer. Output JSON only.",
            repair_system_prompt="You are a strict JSON repair tool. Output JSON only.",
            pydantic_model=TimelineShotPlan,
            extractor=coerce_timeline_shot_plan_payload,
            extra_validator=lambda normalized: plan_mismatch_errors(
                validate_timeline_shot_plan_matches(normalized, batch_spec)
            ),
            max_repairs=2,
            max_tokens=max_tokens,
            stream=False,
        )
        normalized = result.get("normalized")
        if not isinstance(normalized, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=invalid_batch_detail(
                    result,
                    batch_index=batch_index,
                    batch_count=batch_count,
                    clip_ids=clip_ids,
                    max_tokens=max_tokens,
                ),
            )

        attempt = last_attempt(result)
        return {
            "shots": normalized["shots"],
            "provider": attempt.get("provider_used"),
            "model": attempt.get("model_used") or payload.model,
            "usage": attempt.get("usage"),
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
