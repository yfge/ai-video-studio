from datetime import datetime

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")


class MediaAsset(SoftDeleteBusinessMixin, Base):
    """Persisted media artifact addressable by timeline clips and render jobs."""

    __tablename__ = "media_assets"
    __table_args__ = (
        Index("ix_media_assets_asset_type", "asset_type"),
        Index("ix_media_assets_origin", "origin"),
        Index("ix_media_assets_hash", "hash"),
        Index("ix_media_assets_created_by", "created_by"),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True, index=True)
    asset_type = Column(
        String(32), nullable=False, comment="image/video/audio/subtitle"
    )
    origin = Column(String(32), nullable=False, comment="provider/upload/render/import")
    file_url = Column(Text, nullable=True, comment="Public or CDN URL")
    object_key = Column(String(512), nullable=True, comment="OSS/object storage key")
    file_path = Column(String(1024), nullable=True, comment="Local or mounted path")
    mime_type = Column(String(128), nullable=True)
    hash = Column(String(128), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    creator = relationship("User", foreign_keys=[created_by])


class Timeline(SoftDeleteBusinessMixin, Base):
    """Episode-level final editorial timeline spec."""

    __tablename__ = "timelines"
    __table_args__ = (
        Index("ix_timelines_episode_id", "episode_id"),
        Index("ix_timelines_episode_business_id", "episode_business_id"),
        Index("ix_timelines_script_id", "script_id"),
        Index("ix_timelines_script_business_id", "script_business_id"),
        Index("ix_timelines_status", "status"),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    episode_business_id = Column(String(32), nullable=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    script_business_id = Column(String(32), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="draft")
    spec = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    source_audio_timeline_version = Column(Integer, nullable=True)
    rollback_of_version = Column(Integer, nullable=True)
    rollback_target_version = Column(Integer, nullable=True)
    rolled_back_at = Column(DateTime(timezone=True), nullable=True)
    rolled_back_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    episode = relationship("Episode")
    script = relationship("Script")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    rollback_user = relationship("User", foreign_keys=[rolled_back_by])
    render_jobs = relationship("RenderJob", back_populates="timeline")
    revisions = relationship("TimelineRevision", back_populates="timeline")
    clip_assets = relationship("TimelineClipAsset", back_populates="timeline")


class TimelineRevision(Base):
    """Immutable snapshot of one persisted Timeline version."""

    __tablename__ = "timeline_revisions"
    __table_args__ = (
        Index(
            "ux_timeline_revisions_timeline_version",
            "timeline_id",
            "timeline_version",
            unique=True,
        ),
        Index("ix_timeline_revisions_timeline_id", "timeline_id"),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True, index=True)
    timeline_id = Column(BIGINT_PK, ForeignKey("timelines.id"), nullable=False)
    timeline_version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    spec = Column(JSON, nullable=False)
    source_audio_timeline_version = Column(Integer, nullable=True)
    reason = Column(String(64), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    timeline = relationship("Timeline", back_populates="revisions")
    creator = relationship("User", foreign_keys=[created_by])


class RenderJob(SoftDeleteBusinessMixin, Base):
    """Idempotent render/export request for a locked timeline version."""

    __tablename__ = "render_jobs"
    __table_args__ = (
        Index(
            "ux_render_jobs_idempotency",
            "timeline_id",
            "timeline_version",
            "render_type",
            "preset_hash",
            "is_deleted",
            unique=True,
        ),
        Index("ix_render_jobs_status", "status"),
        Index("ix_render_jobs_created_by", "created_by"),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True, index=True)
    timeline_id = Column(BIGINT_PK, ForeignKey("timelines.id"), nullable=False)
    timeline_version = Column(Integer, nullable=False)
    render_type = Column(String(32), nullable=False, comment="proxy/final/export")
    preset_hash = Column(String(64), nullable=False)
    preset = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="queued")
    progress = Column(Integer, nullable=False, default=0)
    output_asset_id = Column(BIGINT_PK, ForeignKey("media_assets.id"), nullable=True)
    log = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    timeline = relationship("Timeline", back_populates="render_jobs")
    output_asset = relationship("MediaAsset")
    creator = relationship("User", foreign_keys=[created_by])
    clip_assets = relationship("TimelineClipAsset", back_populates="render_job")


class TimelineClipAsset(SoftDeleteBusinessMixin, Base):
    """Media asset linked to a stable Timeline clip identity."""

    __tablename__ = "timeline_clip_assets"
    __table_args__ = (
        Index("ix_timeline_clip_assets_timeline", "timeline_id", "timeline_version"),
        Index("ix_timeline_clip_assets_clip_id", "clip_id"),
        Index("ix_timeline_clip_assets_media_asset_id", "media_asset_id"),
        Index("ix_timeline_clip_assets_asset_role", "asset_role"),
        Index(
            "ux_timeline_clip_assets_active",
            "timeline_id",
            "timeline_version",
            "clip_id",
            "asset_role",
            "media_asset_id",
            "is_deleted",
            unique=True,
        ),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True, index=True)
    timeline_id = Column(BIGINT_PK, ForeignKey("timelines.id"), nullable=False)
    timeline_version = Column(Integer, nullable=False)
    clip_id = Column(String(128), nullable=False)
    track_type = Column(String(32), nullable=True)
    asset_role = Column(String(64), nullable=False)
    media_asset_id = Column(BIGINT_PK, ForeignKey("media_assets.id"), nullable=False)
    render_job_id = Column(BIGINT_PK, ForeignKey("render_jobs.id"), nullable=True)
    source = Column(String(64), nullable=True)
    source_ref = Column(JSON, nullable=True)
    replacement_of_id = Column(
        BIGINT_PK,
        ForeignKey("timeline_clip_assets.id"),
        nullable=True,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    timeline = relationship("Timeline", back_populates="clip_assets")
    media_asset = relationship("MediaAsset")
    render_job = relationship("RenderJob", back_populates="clip_assets")
    replacement_of = relationship("TimelineClipAsset", remote_side=[id])
    creator = relationship("User", foreign_keys=[created_by])
