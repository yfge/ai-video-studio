from __future__ import annotations

from copy import deepcopy
from datetime import datetime
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
from app.services.timeline_spec_validation import validate_timeline_spec
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session


class TimelineShot(BaseModel):
    clip_id: str
    duration_ms: int = Field(..., ge=1)
    plot: str = Field(..., min_length=1)
    dialogue_source: str = Field(..., min_length=1)
    visual_prompt: str = Field(..., min_length=1)
    video_prompt: str = Field(..., min_length=1)
    character_anchor: str = Field(..., min_length=1)
    camera: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class TimelineShotPlan(BaseModel):
    shots: list[TimelineShot] = Field(..., min_length=1)


SHOT_PLAN_SCHEMA = TimelineShotPlan.model_json_schema()


class TimelineShotPlanService:
    def __init__(self, db: Session, *, ai_manager: Any | None = None):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.revisions = TimelineRevisionService(db)
        self.clip_lineage = TimelineClipAssetLineageService(db)
        self.ai_manager = ai_manager if ai_manager is not None else ai_service.ai_manager

    async def generate_shot_plan(
        self,
        timeline_id: int,
        payload: TimelineShotPlanRequest,
        current_user: User,
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
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
        video_clips = _clips_for_track(spec, "video")
        if not video_clips:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline video clips missing",
            )

        plan = await self._generate_plan(spec, payload)
        updated_spec = _apply_shot_plan(
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
            user_id=current_user.id,
        )
        timeline.spec = updated_spec
        timeline.version = next_version
        timeline.updated_by = current_user.id
        timeline.rollback_of_version = None
        timeline.rollback_target_version = None
        timeline.rolled_back_at = None
        timeline.rolled_back_by = None
        timeline.spec = self.revisions.spec_with_identity(timeline)
        self.clip_lineage.sync_timeline_assets(timeline, user_id=current_user.id)
        self.revisions.ensure_revision(
            timeline,
            reason="shot_plan_generated",
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    async def _generate_plan(
        self,
        spec: dict[str, Any],
        payload: TimelineShotPlanRequest,
    ) -> dict[str, Any]:
        response = await self.ai_manager.generate_text(
            prompt=_build_prompt(spec, style=payload.style),
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
        _validate_plan_matches_timeline(normalized, spec)
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


def _build_prompt(spec: dict[str, Any], *, style: str) -> str:
    clips = _timeline_prompt_clips(spec)
    return (
        "Return only valid JSON. Generate a Timeline-native shot plan for every "
        "video clip below. Do not change clip_id, timing, or duration_ms. Use only "
        "the provided Timeline fields as story source. The output schema is: "
        '{"shots":[{"clip_id":str,"duration_ms":int,"plot":str,'
        '"dialogue_source":str,"visual_prompt":str,"video_prompt":str,'
        '"character_anchor":str,"camera":str,"action":str}]}. '
        f"Style must be {style}; use non-real cartoon characters only. "
        "Each video_prompt must include plot, dialogue_source, character_anchor, "
        "camera, action, style, and duration. Timeline clips: "
        f"{clips}"
    )


def _timeline_prompt_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    dialogue_by_key = _clips_by_scene_beat(spec, "dialogue")
    subtitle_by_key = _clips_by_scene_beat(spec, "subtitle")
    prompt_clips: list[dict[str, Any]] = []
    for clip in _clips_for_track(spec, "video"):
        key = _scene_beat_key(clip)
        dialogue_clip = dialogue_by_key.get(key) or {}
        subtitle_clip = subtitle_by_key.get(key) or {}
        prompt_clips.append(
            {
                "clip_id": clip.get("clip_id"),
                "scene_id": clip.get("scene_id"),
                "beat_id": clip.get("beat_id"),
                "ordinal": clip.get("ordinal"),
                "start_ms": clip.get("start_ms"),
                "end_ms": clip.get("end_ms"),
                "duration_ms": clip.get("duration_ms"),
                "plot": clip.get("text") or dialogue_clip.get("text") or "",
                "dialogue": dialogue_clip.get("text") or subtitle_clip.get("text") or "",
                "speaker_name": dialogue_clip.get("speaker_name"),
                "dialogue_action": dialogue_clip.get("dialogue_action"),
                "dialogue_emotion": dialogue_clip.get("dialogue_emotion"),
            }
        )
    return prompt_clips


def _validate_plan_matches_timeline(plan: dict[str, Any], spec: dict[str, Any]) -> None:
    video_by_id = {str(clip.get("clip_id")): clip for clip in _clips_for_track(spec, "video")}
    shot_by_id = {str(shot.get("clip_id")): shot for shot in plan.get("shots") or []}
    missing = sorted(set(video_by_id) - set(shot_by_id))
    extra = sorted(set(shot_by_id) - set(video_by_id))
    if missing or extra:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "timeline shot plan clip mismatch",
                "missing": missing,
                "extra": extra,
            },
        )
    for clip_id, shot in shot_by_id.items():
        expected = int(video_by_id[clip_id].get("duration_ms") or 0)
        if int(shot.get("duration_ms") or 0) != expected:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "timeline shot plan duration mismatch",
                    "clip_id": clip_id,
                    "expected_duration_ms": expected,
                    "actual_duration_ms": shot.get("duration_ms"),
                },
            )


def _apply_shot_plan(
    spec: dict[str, Any],
    plan: dict[str, Any],
    *,
    provider: str | None,
    model: str | None,
    style: str,
) -> dict[str, Any]:
    updated = deepcopy(spec)
    generated_at = datetime.utcnow().isoformat() + "Z"
    shot_by_id = {str(shot["clip_id"]): shot for shot in plan["shots"]}
    for clip in _clips_for_track(updated, "video"):
        clip_id = str(clip.get("clip_id"))
        shot = shot_by_id[clip_id]
        refs = clip.setdefault("source_refs", {})
        if not isinstance(refs, dict):
            refs = {}
            clip["source_refs"] = refs
        refs["timeline_shot_plan"] = {
            **shot,
            "style": style,
            "provider": provider,
            "model": model,
            "generated_at": generated_at,
            "source": "timeline_spec",
        }
        refs["provider_chain_stage"] = "timeline_shot_plan_generated"

    source = updated.setdefault("source", {})
    if isinstance(source, dict):
        source["timeline_shot_plan"] = {
            "style": style,
            "provider": provider,
            "model": model,
            "generated_at": generated_at,
            "clip_count": len(plan["shots"]),
        }
    return updated


def _clips_for_track(spec: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    tracks = spec.get("tracks")
    if not isinstance(tracks, list):
        return []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") == track_type or track.get("type") == track_type:
            clips = track.get("clips")
            return [clip for clip in clips or [] if isinstance(clip, dict)]
    return []


def _clips_by_scene_beat(
    spec: dict[str, Any],
    track_type: str,
) -> dict[tuple[Any, Any, Any], dict[str, Any]]:
    return {_scene_beat_key(clip): clip for clip in _clips_for_track(spec, track_type)}


def _scene_beat_key(clip: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (clip.get("scene_id"), clip.get("beat_id"), clip.get("ordinal"))
