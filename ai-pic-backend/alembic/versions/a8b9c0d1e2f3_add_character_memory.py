"""Add character memories, immutable snapshots, and manual promotions.

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-07-23 10:05:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _identity() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.String(32), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.Integer()),
        sa.Column("deleted_reason", sa.Text()),
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


def _create_memories() -> None:
    op.create_table(
        "character_memories",
        *_identity(),
        sa.Column("story_id", sa.Integer()),
        sa.Column("story_business_id", sa.String(32)),
        sa.Column(
            "canon_branch_id", sa.String(32), nullable=False, server_default="main"
        ),
        sa.Column("character_business_id", sa.String(32)),
        sa.Column("virtual_ip_id", sa.Integer(), nullable=False),
        sa.Column("virtual_ip_business_id", sa.String(32), nullable=False),
        sa.Column(
            "scope", sa.String(24), nullable=False, server_default="story_private"
        ),
        sa.Column("memory_type", sa.String(24), nullable=False),
        sa.Column("event_business_id", sa.String(32)),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("belief", sa.Text()),
        sa.Column("belief_confidence", sa.Float()),
        sa.Column("perception", sa.Text()),
        sa.Column("emotional_impact", sa.JSON()),
        sa.Column("salience", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("occurred_at_anchor_business_id", sa.String(32)),
        sa.Column("learned_at_anchor_business_id", sa.String(32), nullable=False),
        sa.Column("effective_from_anchor_business_id", sa.String(32), nullable=False),
        sa.Column("invalidated_at_anchor_business_id", sa.String(32)),
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
        sa.ForeignKeyConstraint(
            ["virtual_ip_id"], ["virtual_ips.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    indexes = {
        "ix_character_memories_business_id": ["business_id"],
        "ix_character_memories_story_business_id": ["story_business_id"],
        "ix_character_memories_virtual_ip_business_id": ["virtual_ip_business_id"],
        "ix_character_memory_story_character_status": [
            "story_id",
            "character_business_id",
            "scope",
            "status",
        ],
        "ix_character_memory_virtual_ip_version": [
            "virtual_ip_id",
            "canon_branch_id",
            "scope",
            "status",
            "version",
        ],
        "ix_character_memory_effective_anchor": ["effective_from_anchor_business_id"],
        "ix_character_memory_source": ["source_artifact_business_id", "source_hash"],
    }
    for name, columns in indexes.items():
        op.create_index(name, "character_memories", columns)


def _create_snapshots() -> None:
    op.create_table(
        "character_memory_snapshots",
        *_identity(),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("story_business_id", sa.String(32), nullable=False),
        sa.Column(
            "canon_branch_id", sa.String(32), nullable=False, server_default="main"
        ),
        sa.Column("character_business_id", sa.String(32), nullable=False),
        sa.Column("virtual_ip_business_id", sa.String(32), nullable=False),
        sa.Column("as_of_anchor_business_id", sa.String(32), nullable=False),
        sa.Column(
            "shared_baseline_version", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "approved_memory_watermark",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("included_memory_ids", sa.JSON(), nullable=False),
        sa.Column("growth_state", sa.JSON(), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stale_reason", sa.JSON()),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(
        "ix_character_memory_snapshots_business_id",
        "character_memory_snapshots",
        ["business_id"],
    )
    op.create_index(
        "ix_memory_snapshot_story_character_anchor",
        "character_memory_snapshots",
        ["story_id", "character_business_id", "as_of_anchor_business_id"],
    )
    op.create_index(
        "ix_memory_snapshot_hash", "character_memory_snapshots", ["snapshot_hash"]
    )


def _create_promotions() -> None:
    op.create_table(
        "character_memory_promotions",
        *_identity(),
        sa.Column("source_story_id", sa.Integer(), nullable=False),
        sa.Column("source_story_business_id", sa.String(32), nullable=False),
        sa.Column("source_memory_ids", sa.JSON(), nullable=False),
        sa.Column("target_virtual_ip_id", sa.Integer(), nullable=False),
        sa.Column("target_virtual_ip_business_id", sa.String(32), nullable=False),
        sa.Column(
            "canon_branch_id", sa.String(32), nullable=False, server_default="main"
        ),
        sa.Column("candidate_content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("result_shared_memory_business_id", sa.String(32)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.Integer()),
        sa.Column("approved_by", sa.Integer()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["source_story_id"], ["stories.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_virtual_ip_id"], ["virtual_ips.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(
        "ix_character_memory_promotions_business_id",
        "character_memory_promotions",
        ["business_id"],
    )
    op.create_index(
        "ix_character_memory_promotions_source_story_business_id",
        "character_memory_promotions",
        ["source_story_business_id"],
    )
    op.create_index(
        "ix_character_memory_promotions_target_virtual_ip_business_id",
        "character_memory_promotions",
        ["target_virtual_ip_business_id"],
    )
    op.create_index(
        "ix_memory_promotion_target_status",
        "character_memory_promotions",
        ["target_virtual_ip_id", "status"],
    )


def upgrade() -> None:
    _create_memories()
    _create_snapshots()
    _create_promotions()


def downgrade() -> None:
    for table in [
        "character_memory_promotions",
        "character_memory_snapshots",
        "character_memories",
    ]:
        op.drop_table(table)
