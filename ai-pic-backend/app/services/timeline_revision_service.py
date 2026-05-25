"""Timeline version snapshot helpers."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline, TimelineRevision
from app.repositories.timeline_repository import TimelineRevisionRepository
from sqlalchemy.orm import Session


class TimelineRevisionService:
    def __init__(self, db: Session):
        self.db = db
        self.revisions = TimelineRevisionRepository(db)

    def ensure_revision(
        self,
        timeline: Timeline,
        *,
        reason: str,
        user_id: int | None,
    ) -> TimelineRevision:
        existing = self.revisions.get_for_version(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
        )
        if existing is not None:
            return existing
        return self.revisions.create(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            title=timeline.title,
            status=timeline.status,
            spec=self.spec_with_identity(timeline),
            source_audio_timeline_version=timeline.source_audio_timeline_version,
            reason=reason,
            created_by=user_id,
        )

    def get_revision(
        self,
        *,
        timeline_id: int,
        timeline_version: int,
    ) -> TimelineRevision | None:
        return self.revisions.get_for_version(
            timeline_id=timeline_id,
            timeline_version=timeline_version,
        )

    @staticmethod
    def spec_with_identity(timeline: Timeline) -> dict[str, Any]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        return {
            **spec,
            "timeline_id": timeline.id,
            "version": timeline.version,
        }
