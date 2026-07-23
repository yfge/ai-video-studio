"""Story-scoped narrative memory persistence models."""

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func


class NarrativeAnchor(SoftDeleteBusinessMixin, Base):
    __tablename__ = "narrative_anchors"
    __table_args__ = (
        Index(
            "ix_narrative_anchor_story_branch_sequence",
            "story_id",
            "canon_branch_id",
            "narrative_sequence",
        ),
        Index(
            "ix_narrative_anchor_source",
            "source_artifact_business_id",
            "source_hash",
        ),
    )

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    story_business_id = Column(String(32), nullable=False, index=True)
    canon_branch_id = Column(String(32), nullable=False, default="main")
    anchor_type = Column(String(24), nullable=False)
    chapter_business_id = Column(String(32), nullable=True)
    episode_business_id = Column(String(32), nullable=True)
    script_business_id = Column(String(32), nullable=True)
    scene_business_id = Column(String(64), nullable=True)
    beat_id = Column(String(64), nullable=True)
    narrative_sequence = Column(Integer, nullable=False)
    story_time_order = Column(Integer, nullable=True)
    story_time_label = Column(String(128), nullable=True)
    story_time_metadata = Column(JSON, nullable=True)
    after_anchor_business_id = Column(String(32), nullable=True)
    before_anchor_business_id = Column(String(32), nullable=True)
    source_artifact_type = Column(String(32), nullable=False)
    source_artifact_business_id = Column(String(64), nullable=False)
    source_version = Column(Integer, nullable=False, default=1)
    source_hash = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="active")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NarrativeEvent(SoftDeleteBusinessMixin, Base):
    __tablename__ = "narrative_events"
    __table_args__ = (
        Index(
            "ix_narrative_event_story_branch_status",
            "story_id",
            "canon_branch_id",
            "status",
        ),
        Index(
            "ix_narrative_event_source", "source_artifact_business_id", "source_hash"
        ),
    )

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    story_business_id = Column(String(32), nullable=False, index=True)
    canon_branch_id = Column(String(32), nullable=False, default="main")
    event_type = Column(String(32), nullable=False)
    summary = Column(Text, nullable=False)
    participant_character_ids = Column(JSON, nullable=True)
    occurred_at_anchor_business_id = Column(String(32), nullable=False)
    presentation = Column(String(24), nullable=False, default="on_screen")
    audience_disclosure = Column(String(24), nullable=False, default="revealed")
    status = Column(String(24), nullable=False, default="candidate")
    source_artifact_type = Column(String(32), nullable=False)
    source_artifact_business_id = Column(String(64), nullable=False)
    source_version = Column(Integer, nullable=False, default=1)
    source_hash = Column(String(64), nullable=False)
    candidate_evidence = Column(JSON, nullable=True)
    invalidation = Column(JSON, nullable=True)
    supersedes_business_id = Column(String(32), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CharacterMemory(SoftDeleteBusinessMixin, Base):
    __tablename__ = "character_memories"
    __table_args__ = (
        Index(
            "ix_character_memory_story_character_status",
            "story_id",
            "character_business_id",
            "scope",
            "status",
        ),
        Index(
            "ix_character_memory_virtual_ip_version",
            "virtual_ip_id",
            "canon_branch_id",
            "scope",
            "status",
            "version",
        ),
        Index(
            "ix_character_memory_effective_anchor", "effective_from_anchor_business_id"
        ),
        Index(
            "ix_character_memory_source", "source_artifact_business_id", "source_hash"
        ),
    )

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    story_business_id = Column(String(32), nullable=True, index=True)
    canon_branch_id = Column(String(32), nullable=False, default="main")
    character_business_id = Column(String(32), nullable=True)
    virtual_ip_id = Column(Integer, ForeignKey("virtual_ips.id"), nullable=False)
    virtual_ip_business_id = Column(String(32), nullable=False, index=True)
    scope = Column(String(24), nullable=False, default="story_private")
    memory_type = Column(String(24), nullable=False)
    event_business_id = Column(String(32), nullable=True)
    content = Column(Text, nullable=False)
    belief = Column(Text, nullable=True)
    belief_confidence = Column(Float, nullable=True)
    perception = Column(Text, nullable=True)
    emotional_impact = Column(JSON, nullable=True)
    salience = Column(Float, nullable=False, default=0.5)
    occurred_at_anchor_business_id = Column(String(32), nullable=True)
    learned_at_anchor_business_id = Column(String(32), nullable=False)
    effective_from_anchor_business_id = Column(String(32), nullable=False)
    invalidated_at_anchor_business_id = Column(String(32), nullable=True)
    status = Column(String(24), nullable=False, default="candidate")
    source_artifact_type = Column(String(32), nullable=False)
    source_artifact_business_id = Column(String(64), nullable=False)
    source_version = Column(Integer, nullable=False, default=1)
    source_hash = Column(String(64), nullable=False)
    candidate_evidence = Column(JSON, nullable=True)
    invalidation = Column(JSON, nullable=True)
    supersedes_business_id = Column(String(32), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CharacterMemorySnapshot(SoftDeleteBusinessMixin, Base):
    __tablename__ = "character_memory_snapshots"
    __table_args__ = (
        Index(
            "ix_memory_snapshot_story_character_anchor",
            "story_id",
            "character_business_id",
            "as_of_anchor_business_id",
        ),
        Index("ix_memory_snapshot_hash", "snapshot_hash"),
    )

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    story_business_id = Column(String(32), nullable=False, index=True)
    canon_branch_id = Column(String(32), nullable=False, default="main")
    character_business_id = Column(String(32), nullable=False)
    virtual_ip_business_id = Column(String(32), nullable=False)
    as_of_anchor_business_id = Column(String(32), nullable=False)
    shared_baseline_version = Column(Integer, nullable=False, default=0)
    approved_memory_watermark = Column(Integer, nullable=False, default=0)
    included_memory_ids = Column(JSON, nullable=False)
    growth_state = Column(JSON, nullable=False)
    snapshot_hash = Column(String(64), nullable=False)
    is_stale = Column(Boolean, nullable=False, default=False)
    stale_reason = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CharacterMemoryPromotion(SoftDeleteBusinessMixin, Base):
    __tablename__ = "character_memory_promotions"
    __table_args__ = (
        Index(
            "ix_memory_promotion_target_status",
            "target_virtual_ip_id",
            "status",
        ),
    )

    id = Column(Integer, primary_key=True)
    source_story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    source_story_business_id = Column(String(32), nullable=False, index=True)
    source_memory_ids = Column(JSON, nullable=False)
    target_virtual_ip_id = Column(Integer, ForeignKey("virtual_ips.id"), nullable=False)
    target_virtual_ip_business_id = Column(String(32), nullable=False, index=True)
    canon_branch_id = Column(String(32), nullable=False, default="main")
    candidate_content = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="pending")
    decision_reason = Column(Text, nullable=True)
    result_shared_memory_business_id = Column(String(32), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
