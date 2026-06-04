from typing import List, Optional

from app.models.script import Episode, Story
from app.models.timeline import (
    MediaAsset,
    RenderJob,
    Timeline,
    TimelineClipAsset,
    TimelineRevision,
)
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session, joinedload


class TimelineRepository(BaseRepository[Timeline]):
    """Timeline persistence with episode/story access filtering."""

    def __init__(self, session: Session):
        super().__init__(Timeline, session)

    def get_by_id_for_update(self, timeline_id: int) -> Optional[Timeline]:
        return (
            self.session.query(Timeline)
            .filter(Timeline.id == timeline_id)
            .populate_existing()
            .with_for_update()
            .first()
        )

    def list_for_episode(
        self,
        episode_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
        limit: int = 50,
    ) -> List[Timeline]:
        query = (
            self.session.query(Timeline)
            .join(Episode, Timeline.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .options(joinedload(Timeline.episode), joinedload(Timeline.script))
            .filter(Timeline.episode_id == episode_id)
        )

        if not include_deleted:
            query = query.filter(Timeline.is_deleted.is_(False))
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return (
            query.order_by(Timeline.updated_at.desc(), Timeline.id.desc())
            .limit(limit)
            .all()
        )

    def get_accessible(
        self,
        timeline_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> Optional[Timeline]:
        query = (
            self.session.query(Timeline)
            .join(Episode, Timeline.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .options(
                joinedload(Timeline.episode).joinedload(Episode.story),
                joinedload(Timeline.script),
            )
            .filter(Timeline.id == timeline_id)
        )

        if not include_deleted:
            query = query.filter(Timeline.is_deleted.is_(False))
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return query.first()

    def get_latest_for_episode_script(
        self,
        *,
        episode_id: int,
        script_id: int,
        include_deleted: bool = False,
    ) -> Optional[Timeline]:
        query = (
            self.session.query(Timeline)
            .filter(Timeline.episode_id == episode_id)
            .filter(Timeline.script_id == script_id)
        )
        if not include_deleted:
            query = query.filter(Timeline.is_deleted.is_(False))
        return query.order_by(Timeline.version.desc(), Timeline.id.desc()).first()


class TimelineRevisionRepository(BaseRepository[TimelineRevision]):
    """Immutable Timeline version snapshots used for rollback."""

    def __init__(self, session: Session):
        super().__init__(TimelineRevision, session)

    def get_for_version(
        self,
        *,
        timeline_id: int,
        timeline_version: int,
    ) -> Optional[TimelineRevision]:
        return (
            self.session.query(TimelineRevision)
            .filter(TimelineRevision.timeline_id == timeline_id)
            .filter(TimelineRevision.timeline_version == timeline_version)
            .first()
        )


class MediaAssetRepository(BaseRepository[MediaAsset]):
    """Media asset persistence for timeline and render artifacts."""

    def __init__(self, session: Session):
        super().__init__(MediaAsset, session)

    def find_by_location(
        self,
        *,
        asset_type: str,
        file_url: str | None = None,
        file_path: str | None = None,
        object_key: str | None = None,
    ) -> Optional[MediaAsset]:
        query = self.session.query(MediaAsset).filter(
            MediaAsset.asset_type == asset_type,
            MediaAsset.is_deleted.is_(False),
        )
        if object_key:
            return query.filter(MediaAsset.object_key == object_key).first()
        if file_url:
            return query.filter(MediaAsset.file_url == file_url).first()
        if file_path:
            return query.filter(MediaAsset.file_path == file_path).first()
        return None


class TimelineClipAssetRepository(BaseRepository[TimelineClipAsset]):
    """Clip-to-asset lineage persistence."""

    def __init__(self, session: Session):
        super().__init__(TimelineClipAsset, session)

    def list_for_timeline(
        self,
        *,
        timeline_id: int,
        timeline_version: int | None = None,
        clip_id: str | None = None,
        include_deleted: bool = False,
    ) -> List[TimelineClipAsset]:
        query = self.session.query(TimelineClipAsset).filter(
            TimelineClipAsset.timeline_id == timeline_id
        )
        if timeline_version is not None:
            query = query.filter(TimelineClipAsset.timeline_version == timeline_version)
        if clip_id:
            query = query.filter(TimelineClipAsset.clip_id == clip_id)
        if not include_deleted:
            query = query.filter(TimelineClipAsset.is_deleted.is_(False))
        return query.order_by(
            TimelineClipAsset.timeline_version.desc(),
            TimelineClipAsset.clip_id.asc(),
            TimelineClipAsset.asset_role.asc(),
            TimelineClipAsset.id.asc(),
        ).all()

    def get_active_link(
        self,
        *,
        timeline_id: int,
        timeline_version: int,
        clip_id: str,
        asset_role: str,
        media_asset_id: int,
    ) -> Optional[TimelineClipAsset]:
        return (
            self.session.query(TimelineClipAsset)
            .filter(TimelineClipAsset.timeline_id == timeline_id)
            .filter(TimelineClipAsset.timeline_version == timeline_version)
            .filter(TimelineClipAsset.clip_id == clip_id)
            .filter(TimelineClipAsset.asset_role == asset_role)
            .filter(TimelineClipAsset.media_asset_id == media_asset_id)
            .filter(TimelineClipAsset.is_deleted.is_(False))
            .first()
        )

    def get_latest_for_clip_role(
        self,
        *,
        timeline_id: int,
        timeline_version: int,
        clip_id: str,
        asset_role: str,
    ) -> Optional[TimelineClipAsset]:
        return (
            self.session.query(TimelineClipAsset)
            .filter(TimelineClipAsset.timeline_id == timeline_id)
            .filter(TimelineClipAsset.timeline_version == timeline_version)
            .filter(TimelineClipAsset.clip_id == clip_id)
            .filter(TimelineClipAsset.asset_role == asset_role)
            .filter(TimelineClipAsset.is_deleted.is_(False))
            .order_by(TimelineClipAsset.id.desc())
            .first()
        )


class RenderJobRepository(BaseRepository[RenderJob]):
    """Render job persistence with idempotency lookup."""

    def __init__(self, session: Session):
        super().__init__(RenderJob, session)

    def list_for_timeline(
        self, timeline_id: int, include_deleted: bool = False, limit: int = 50
    ) -> List[RenderJob]:
        query = self.session.query(RenderJob).filter(
            RenderJob.timeline_id == timeline_id
        )
        if not include_deleted:
            query = query.filter(RenderJob.is_deleted.is_(False))
        return (
            query.order_by(RenderJob.created_at.desc(), RenderJob.id.desc())
            .limit(limit)
            .all()
        )

    def get_idempotent(
        self,
        *,
        timeline_id: int,
        timeline_version: int,
        render_type: str,
        preset_hash: str,
    ) -> Optional[RenderJob]:
        return (
            self.session.query(RenderJob)
            .filter(RenderJob.timeline_id == timeline_id)
            .filter(RenderJob.timeline_version == timeline_version)
            .filter(RenderJob.render_type == render_type)
            .filter(RenderJob.preset_hash == preset_hash)
            .filter(RenderJob.is_deleted.is_(False))
            .first()
        )

    def get_for_timeline(
        self,
        *,
        timeline_id: int,
        render_job_id: int,
        include_deleted: bool = False,
    ) -> Optional[RenderJob]:
        query = (
            self.session.query(RenderJob)
            .filter(RenderJob.timeline_id == timeline_id)
            .filter(RenderJob.id == render_job_id)
        )
        if not include_deleted:
            query = query.filter(RenderJob.is_deleted.is_(False))
        return query.first()
