"""add_story_structure_tables

Revision ID: a1b2c3d4e5f6
Revises: fe284ccd1b92
Create Date: 2025-10-17 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "fe284ccd1b92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create normalized narrative structure tables."""
    op.create_table(
        "story_treatments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("story_id", sa.Integer(), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("logline", sa.Text(), nullable=True),
        sa.Column("theme_summary", sa.Text(), nullable=True),
        sa.Column("act_structure", sa.JSON(), nullable=True, comment="Act I/II/III structured summary"),
        sa.Column("target_audience_notes", sa.Text(), nullable=True),
        sa.Column("tone_reference", sa.JSON(), nullable=True, comment="Visual/audio references"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ai_prompt_snapshot", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ux_story_treatments_story_revision",
        "story_treatments",
        ["story_id", "revision_number"],
        unique=True,
    )

    op.create_table(
        "story_step_outlines",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("story_id", sa.Integer(), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "story_treatment_id",
            sa.BigInteger(),
            sa.ForeignKey("story_treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("act_label", sa.String(length=50), nullable=True),
        sa.Column("beat_title", sa.String(length=255), nullable=False),
        sa.Column("beat_summary", sa.Text(), nullable=True),
        sa.Column("dramatic_question", sa.Text(), nullable=True),
        sa.Column("characters_involved", sa.JSON(), nullable=True),
        sa.Column("location_hint", sa.String(length=255), nullable=True),
        sa.Column("duration_estimate_minutes", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ux_step_outlines_treatment_sequence",
        "story_step_outlines",
        ["story_treatment_id", "sequence_number"],
        unique=True,
    )

    op.create_table(
        "scenes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("script_id", sa.Integer(), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "story_step_outline_id",
            sa.BigInteger(),
            sa.ForeignKey("story_step_outlines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scene_number", sa.String(length=20), nullable=False),
        sa.Column("slug_line", sa.String(length=255), nullable=False),
        sa.Column("environment_type", sa.String(length=32), nullable=True, comment="INT/EXT/INT-EXT"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("time_of_day", sa.String(length=50), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("page_length_eighths", sa.Integer(), nullable=True),
        sa.Column("primary_characters", sa.JSON(), nullable=True),
        sa.Column("conflict_notes", sa.Text(), nullable=True),
        sa.Column("ai_prompt_snapshot", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ux_scenes_script_scene_number",
        "scenes",
        ["script_id", "scene_number"],
        unique=True,
    )

    op.create_table(
        "scene_beats",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scene_id", sa.BigInteger(), sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("beat_type", sa.String(length=32), nullable=True),
        sa.Column("beat_summary", sa.Text(), nullable=True),
        sa.Column("characters_involved", sa.JSON(), nullable=True),
        sa.Column("dialogue_excerpt", sa.Text(), nullable=True),
        sa.Column("camera_notes", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(6, 2), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ux_scene_beats_scene_order",
        "scene_beats",
        ["scene_id", "order_index"],
        unique=True,
    )

    op.create_table(
        "shots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scene_id", sa.BigInteger(), sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "scene_beat_id",
            sa.BigInteger(),
            sa.ForeignKey("scene_beats.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("shot_number", sa.String(length=20), nullable=False),
        sa.Column("shot_type", sa.String(length=50), nullable=True),
        sa.Column("camera_setup", sa.String(length=255), nullable=True),
        sa.Column("camera_movement", sa.String(length=50), nullable=True),
        sa.Column("framing", sa.Text(), nullable=True),
        sa.Column("focus_subject", sa.String(length=255), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(6, 2), nullable=True),
        sa.Column("storyboard_frame_asset_id", sa.Integer(), sa.ForeignKey("images.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lighting_notes", sa.Text(), nullable=True),
        sa.Column("audio_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ux_shots_scene_shot_number",
        "shots",
        ["scene_id", "shot_number"],
        unique=True,
    )


def downgrade() -> None:
    """Drop narrative structure tables."""
    op.drop_index("ux_shots_scene_shot_number", table_name="shots")
    op.drop_table("shots")
    op.drop_index("ux_scene_beats_scene_order", table_name="scene_beats")
    op.drop_table("scene_beats")
    op.drop_index("ux_scenes_script_scene_number", table_name="scenes")
    op.drop_table("scenes")
    op.drop_index("ux_step_outlines_treatment_sequence", table_name="story_step_outlines")
    op.drop_table("story_step_outlines")
    op.drop_index("ux_story_treatments_story_revision", table_name="story_treatments")
    op.drop_table("story_treatments")

