from typing import List, Optional

from app.models.script import Episode, Script
from app.models.timeline import Timeline
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
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_render_dispatch import dispatch_timeline_render_job
from app.services.timeline_render_hash import render_preset_hash
from app.services.timeline_responses import render_job_response, timeline_response
from app.services.timeline_revision_service import TimelineRevisionService
from app.services.timeline_spec_api_guard import (
    validate_new_timeline_spec_or_400,
    validate_persisted_timeline_spec_or_400,
    validated_timeline_update_payload_or_400,
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
        self.revisions = TimelineRevisionService(db)
        self.clip_lineage = TimelineClipAssetLineageService(db)

    def list_timelines(
        self, episode_id: int, current_user: User
    ) -> List[TimelineResponse]:
        self._get_episode_or_404(episode_id, current_user)
        items = self.timelines.list_for_episode(
            episode_id=episode_id,
            user_id=self._story_owner_filter(current_user),
        )
        return [timeline_response(item) for item in items]

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
        validate_new_timeline_spec_or_400(payload.spec, episode=episode, script=script)

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
        timeline.spec = self.revisions.spec_with_identity(timeline)
        validate_persisted_timeline_spec_or_400(timeline)
        self.clip_lineage.sync_timeline_assets(timeline, user_id=current_user.id)
        self.revisions.ensure_revision(
            timeline,
            reason="created",
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    def get_timeline(self, timeline_id: int, current_user: User) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        return timeline_response(timeline)

    def update_timeline(
        self, timeline_id: int, payload: TimelineUpdate, current_user: User
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )
        self.revisions.ensure_revision(
            timeline,
            reason="pre_update_snapshot",
            user_id=current_user.id,
        )

        updates, next_version = validated_timeline_update_payload_or_400(
            timeline,
            payload,
        )
        for field, value in updates.items():
            setattr(timeline, field, value)
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
            reason="updated",
            user_id=current_user.id,
        )

        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    def queue_render_job(
        self, timeline_id: int, payload: RenderJobCreate, current_user: User
    ) -> RenderJobResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.timeline_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="render job timeline_version must match current timeline version",
            )

        preset_hash = render_preset_hash(payload.preset)
        existing = self.render_jobs.get_idempotent(
            timeline_id=timeline.id,
            timeline_version=payload.timeline_version,
            render_type=payload.render_type,
            preset_hash=preset_hash,
        )
        if existing is not None:
            if payload.force_new_attempt:
                if existing.status not in {"failed", "cancelled"}:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "force_new_attempt is only allowed for failed "
                            "or cancelled render jobs"
                        ),
                    )
                existing.soft_delete(
                    user_id=current_user.id,
                    reason="force_new_attempt",
                )
                self.db.flush()
            else:
                return render_job_response(existing)

        if existing is not None and payload.force_new_attempt:
            # Existing failed/cancelled job was soft-deleted above so the
            # idempotency constraint allows one fresh active attempt.
            existing = None

        if existing is not None:
            return render_job_response(existing)

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
        dispatch_timeline_render_job(job, current_user)
        self.db.refresh(job)
        return render_job_response(job)

    def list_render_jobs(
        self,
        timeline_id: int,
        current_user: User,
        *,
        include_deleted: bool = False,
    ) -> List[RenderJobResponse]:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        items = self.render_jobs.list_for_timeline(
            timeline.id,
            include_deleted=include_deleted,
        )
        return [render_job_response(item) for item in items]

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
