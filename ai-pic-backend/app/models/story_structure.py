from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Numeric,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")


class StoryTreatment(Base):
    """Normalized story-wide treatment/revision metadata.

    Mirrors alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py
    table definition for `story_treatments`.
    """

    __tablename__ = "story_treatments"

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    story_id = Column(
        Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    revision_number = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="draft")
    title = Column(String(255), nullable=False)
    logline = Column(Text)
    theme_summary = Column(Text)
    act_structure = Column(JSON, comment="Act I/II/III structured summary")
    target_audience_notes = Column(Text)
    tone_reference = Column(JSON, comment="Visual/audio references")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    ai_prompt_snapshot = Column(JSON)
    extra_metadata = Column("metadata", JSON)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relations
    story = relationship("Story", backref="story_treatments")
    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])


class StoryStepOutline(Base):
    """Beat-level outline scoped to a treatment (optionally an episode)."""

    __tablename__ = "story_step_outlines"

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    story_id = Column(
        Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    episode_id = Column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True
    )
    story_treatment_id = Column(
        BIGINT_PK, ForeignKey("story_treatments.id", ondelete="CASCADE"), nullable=False
    )
    sequence_number = Column(Integer, nullable=False)
    act_label = Column(String(50))
    beat_title = Column(String(255), nullable=False)
    beat_summary = Column(Text)
    dramatic_question = Column(Text)
    characters_involved = Column(JSON)
    location_hint = Column(String(255))
    duration_estimate_minutes = Column(Numeric(5, 2))
    status = Column(String(32), nullable=False, default="draft")
    extra_metadata = Column("metadata", JSON)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relations
    story = relationship("Story", backref="step_outlines")
    episode = relationship("Episode", backref="step_outlines")
    treatment = relationship("StoryTreatment", backref="step_outlines")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])


class Scene(Base):
    """Script-scoped scene record linked optionally to an outline beat."""

    __tablename__ = "scenes"

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    script_id = Column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    story_step_outline_id = Column(
        BIGINT_PK,
        ForeignKey("story_step_outlines.id", ondelete="SET NULL"),
        nullable=True,
    )
    scene_number = Column(String(20), nullable=False)
    slug_line = Column(String(255), nullable=False)
    environment_type = Column(String(32), comment="INT/EXT/INT-EXT")
    location = Column(String(255))
    time_of_day = Column(String(50))
    summary = Column(Text)
    page_length_eighths = Column(Integer)
    primary_characters = Column(JSON)
    conflict_notes = Column(Text)
    ai_prompt_snapshot = Column(JSON)
    status = Column(String(32), nullable=False, default="draft")
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relations
    script = relationship("Script", backref="normalized_scenes")
    step_outline = relationship("StoryStepOutline", backref="scenes")


class SceneBeat(Base):
    """Ordered beat rows inside a scene."""

    __tablename__ = "scene_beats"

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    scene_id = Column(
        BIGINT_PK, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False
    )
    order_index = Column(Integer, nullable=False)
    beat_type = Column(String(32))
    beat_summary = Column(Text)
    characters_involved = Column(JSON)
    dialogue_excerpt = Column(Text)
    camera_notes = Column(Text)
    duration_seconds = Column(Numeric(6, 2))
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relations
    scene = relationship("Scene", backref="beats")


class Shot(Base):
    """Shot planning rows optionally linked to a scene beat and storyboard asset."""

    __tablename__ = "shots"

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    scene_id = Column(
        BIGINT_PK, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False
    )
    scene_beat_id = Column(
        BIGINT_PK, ForeignKey("scene_beats.id", ondelete="SET NULL"), nullable=True
    )
    shot_number = Column(String(20), nullable=False)
    shot_type = Column(String(50))
    camera_setup = Column(String(255))
    camera_movement = Column(String(50))
    framing = Column(Text)
    focus_subject = Column(String(255))
    duration_seconds = Column(Numeric(6, 2))
    storyboard_frame_asset_id = Column(
        Integer, ForeignKey("images.id", ondelete="SET NULL"), nullable=True
    )
    lighting_notes = Column(Text)
    audio_notes = Column(Text)
    status = Column(String(32), nullable=False, default="planned")
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relations
    scene = relationship("Scene", backref="shots")
    beat = relationship("SceneBeat", backref="shots")
    storyboard_image = relationship("Image", backref="referenced_by_shots")
