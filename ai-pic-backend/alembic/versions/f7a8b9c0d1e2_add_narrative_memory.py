"""Add story-scoped narrative memory and Story Seed persistence.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-23 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _identity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
    ]


def _timestamps(*, updated: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        )
    ]
    if updated:
        columns.append(
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            )
        )
    return columns


def _create_anchor_table() -> None:
    op.create_table(
        "narrative_anchors",
        *_identity_columns(),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("story_business_id", sa.String(32), nullable=False),
        sa.Column(
            "canon_branch_id", sa.String(32), nullable=False, server_default="main"
        ),
        sa.Column("anchor_type", sa.String(24), nullable=False),
        sa.Column("chapter_business_id", sa.String(32)),
        sa.Column("episode_business_id", sa.String(32)),
        sa.Column("script_business_id", sa.String(32)),
        sa.Column("scene_business_id", sa.String(64)),
        sa.Column("beat_id", sa.String(64)),
        sa.Column("narrative_sequence", sa.Integer(), nullable=False),
        sa.Column("story_time_order", sa.Integer()),
        sa.Column("story_time_label", sa.String(128)),
        sa.Column("story_time_metadata", sa.JSON()),
        sa.Column("after_anchor_business_id", sa.String(32)),
        sa.Column("before_anchor_business_id", sa.String(32)),
        sa.Column("source_artifact_type", sa.String(32), nullable=False),
        sa.Column("source_artifact_business_id", sa.String(64), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(
        "ix_narrative_anchors_business_id", "narrative_anchors", ["business_id"]
    )
    op.create_index(
        "ix_narrative_anchors_story_business_id",
        "narrative_anchors",
        ["story_business_id"],
    )
    op.create_index(
        "ix_narrative_anchor_story_branch_sequence",
        "narrative_anchors",
        ["story_id", "canon_branch_id", "narrative_sequence"],
    )
    op.create_index(
        "ix_narrative_anchor_source",
        "narrative_anchors",
        ["source_artifact_business_id", "source_hash"],
    )


def _create_event_table() -> None:
    op.create_table(
        "narrative_events",
        *_identity_columns(),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("story_business_id", sa.String(32), nullable=False),
        sa.Column(
            "canon_branch_id", sa.String(32), nullable=False, server_default="main"
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("participant_character_ids", sa.JSON()),
        sa.Column("occurred_at_anchor_business_id", sa.String(32), nullable=False),
        sa.Column(
            "presentation", sa.String(24), nullable=False, server_default="on_screen"
        ),
        sa.Column(
            "audience_disclosure",
            sa.String(24),
            nullable=False,
            server_default="revealed",
        ),
        sa.Column("status", sa.String(24), nullable=False, server_default="candidate"),
        sa.Column("source_artifact_type", sa.String(32), nullable=False),
        sa.Column("source_artifact_business_id", sa.String(64), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("candidate_evidence", sa.JSON()),
        sa.Column("invalidation", sa.JSON()),
        sa.Column("supersedes_business_id", sa.String(32)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.Integer()),
        sa.Column("approved_by", sa.Integer()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(
        "ix_narrative_events_business_id", "narrative_events", ["business_id"]
    )
    op.create_index(
        "ix_narrative_events_story_business_id",
        "narrative_events",
        ["story_business_id"],
    )
    op.create_index(
        "ix_narrative_event_story_branch_status",
        "narrative_events",
        ["story_id", "canon_branch_id", "status"],
    )
    op.create_index(
        "ix_narrative_event_source",
        "narrative_events",
        ["source_artifact_business_id", "source_hash"],
    )


def upgrade() -> None:
    story_columns = [
        ("story_seed", sa.JSON()),
        ("story_seed_schema", sa.String(32), "story_seed_v1"),
        ("story_seed_status", sa.String(24), "draft"),
        ("story_seed_version", sa.Integer(), "1"),
        ("story_seed_updated_at", sa.DateTime()),
        ("memory_mode", sa.String(32), "off"),
        ("canon_branch_id", sa.String(32), "main"),
        ("shared_memory_baseline", sa.JSON()),
        ("shared_memory_baseline_version", sa.Integer(), "0"),
        ("shared_memory_baseline_hash", sa.String(64)),
        ("memory_ledger_version", sa.Integer(), "0"),
        ("memory_ledger_hash", sa.String(64)),
        ("memory_review_status", sa.String(24), "not_initialized"),
    ]
    for spec in story_columns:
        name, column_type, *default = spec
        op.add_column(
            "stories",
            sa.Column(
                name, column_type, server_default=default[0] if default else None
            ),
        )
    for name, column_type, default in [
        ("memory_snapshot_evidence", sa.JSON(), None),
        ("memory_ledger_version", sa.Integer(), None),
        ("memory_ledger_hash", sa.String(64), None),
        ("disclosure_policy", sa.JSON(), None),
        ("memory_snapshot_stale", sa.Boolean(), sa.false()),
        ("memory_snapshot_stale_reason", sa.JSON(), None),
    ]:
        op.add_column("episodes", sa.Column(name, column_type, server_default=default))
    _create_anchor_table()
    _create_event_table()


def downgrade() -> None:
    for table in ["narrative_events", "narrative_anchors"]:
        op.drop_table(table)
    for name in [
        "memory_snapshot_stale_reason",
        "memory_snapshot_stale",
        "disclosure_policy",
        "memory_ledger_hash",
        "memory_ledger_version",
        "memory_snapshot_evidence",
    ]:
        op.drop_column("episodes", name)
    for name in [
        "memory_review_status",
        "memory_ledger_hash",
        "memory_ledger_version",
        "shared_memory_baseline_hash",
        "shared_memory_baseline_version",
        "shared_memory_baseline",
        "canon_branch_id",
        "memory_mode",
        "story_seed_updated_at",
        "story_seed_version",
        "story_seed_status",
        "story_seed_schema",
        "story_seed",
    ]:
        op.drop_column("stories", name)
