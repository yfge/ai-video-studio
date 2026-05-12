import hashlib
import json
from typing import Any, Dict, List, Optional

from app.models.script import Episode, Script
from app.models.timeline import RenderJob, Timeline
from app.models.user import User
from app.repositories.script_repository import EpisodeRepository, ScriptRepository
from app.repositories.timeline_repository import RenderJobRepository, TimelineRepository
from app.schemas.timeline import (
    RenderJobCreate,
    RenderJobResponse,
    TimelineCreate,
    TimelineResponse,
    TimelineUpdate,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineService:
    """Application service for the episode-level Timeline Spec v1 contract."""

    def __init__(self, db: Session):
        self.db = db
        self.episodes = EpisodeRepository(db)
        self.scripts = ScriptRepository(db)
        self.timelines = TimelineRepository(db)
        self.render_jobs = RenderJobRepository(db)

    def list_timelines(
        self, episode_id: int, current_user: User
    ) -> List[TimelineResponse]:
        self._get_episode_or_404(episode_id, current_user)
        items = self.timelines.list_for_episode(
            episode_id=episode_id,
            user_id=self._story_owner_filter(current_user),
        )
        return [self._timeline_response(item) for item in items]

    def create_timeline(
        self, episode_id: int, payload: TimelineCreate, current_user: User
    ) -> TimelineResponse:
        episode = self._get_episode_or_404(episode_id, current_user)
        script = self._get_script_or_404(payload.script_id, current_user)
        if script.episode_id != episode.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline script must belong to the requested episode",
            )

        title = payload.title or f"{episode.title} Timeline"
        timeline = self.timelines.create(
            episode_id=episode.id,
            episode_business_id=episode.business_id,
            script_id=script.id,
            script_business_id=script.business_id,
            title=title,
            status=payload.status,
            spec=payload.spec,
            version=1,
            source_audio_timeline_version=payload.source_audio_timeline_version,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        self.db.flush()
        timeline.spec = self._spec_with_identity(timeline)
        self.db.commit()
        self.db.refresh(timeline)
        return self._timeline_response(timeline)

    def get_timeline(self, timeline_id: int, current_user: User) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        return self._timeline_response(timeline)

    def update_timeline(
        self, timeline_id: int, payload: TimelineUpdate, current_user: User
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )

        updates = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
        for field, value in updates.items():
            setattr(timeline, field, value)
        timeline.version = (timeline.version or 0) + 1
        timeline.updated_by = current_user.id
        timeline.spec = self._spec_with_identity(timeline)

        self.db.commit()
        self.db.refresh(timeline)
        return self._timeline_response(timeline)

    def queue_render_job(
        self, timeline_id: int, payload: RenderJobCreate, current_user: User
    ) -> RenderJobResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.timeline_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="render job timeline_version must match current timeline version",
            )

        preset_hash = self._preset_hash(payload.preset)
        existing = self.render_jobs.get_idempotent(
            timeline_id=timeline.id,
            timeline_version=payload.timeline_version,
            render_type=payload.render_type,
            preset_hash=preset_hash,
        )
        if existing is not None:
            return self._render_job_response(existing)

        job = self.render_jobs.create(
            timeline_id=timeline.id,
            timeline_version=payload.timeline_version,
            render_type=payload.render_type,
            preset_hash=preset_hash,
            preset=payload.preset,
            status="queued",
            progress=0,
            created_by=current_user.id,
        )
        self.db.commit()
        self.db.refresh(job)
        return self._render_job_response(job)

    def list_render_jobs(
        self, timeline_id: int, current_user: User
    ) -> List[RenderJobResponse]:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        items = self.render_jobs.list_for_timeline(timeline.id)
        return [self._render_job_response(item) for item in items]

    def _get_episode_or_404(self, episode_id: int, current_user: User) -> Episode:
        episode = self.episodes.get_with_story(
            episode_id=episode_id,
            user_id=self._story_owner_filter(current_user),
        )
        if episode is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="episode not found",
            )
        return episode

    def _get_script_or_404(self, script_id: int, current_user: User) -> Script:
        script = self.scripts.get_with_relations(
            script_id=script_id,
            user_id=self._story_owner_filter(current_user),
        )
        if script is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="script not found",
            )
        return script

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
    def _story_owner_filter(current_user: User) -> Optional[int]:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id

    @staticmethod
    def _preset_hash(preset: Dict[str, Any]) -> str:
        normalized = json.dumps(
            preset, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _spec_with_identity(timeline: Timeline) -> Dict[str, Any]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        return {
            **spec,
            "timeline_id": timeline.id,
            "version": timeline.version,
        }

    @staticmethod
    def _timeline_response(timeline: Timeline) -> TimelineResponse:
        return TimelineResponse(
            id=timeline.id,
            business_id=timeline.business_id,
            episode_id=timeline.episode_id,
            episode_business_id=timeline.episode_business_id,
            script_id=timeline.script_id,
            script_business_id=timeline.script_business_id,
            title=timeline.title,
            status=timeline.status,
            spec=timeline.spec or {},
            version=timeline.version,
            source_audio_timeline_version=timeline.source_audio_timeline_version,
            created_by=timeline.created_by,
            updated_by=timeline.updated_by,
            created_at=timeline.created_at,
            updated_at=timeline.updated_at,
        )

    @staticmethod
    def _render_job_response(job: RenderJob) -> RenderJobResponse:
        return RenderJobResponse(
            id=job.id,
            business_id=job.business_id,
            timeline_id=job.timeline_id,
            timeline_version=job.timeline_version,
            render_type=job.render_type,
            preset_hash=job.preset_hash,
            preset=job.preset or {},
            status=job.status,
            progress=job.progress,
            output_asset_id=job.output_asset_id,
            log=job.log,
            created_by=job.created_by,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
