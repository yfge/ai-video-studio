"""Add versioned story novel adaptation chain.

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-07-22 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    op.add_column(
        "stories",
        sa.Column(
            "workflow_mode",
            sa.String(length=32),
            nullable=False,
            server_default="direct",
        ),
    )
    op.add_column(
        "stories",
        sa.Column("canonical_novel_export_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_stories_canonical_novel_export_id",
        "stories",
        ["canonical_novel_export_id"],
    )

    op.add_column(
        "story_novel_exports",
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "story_novel_exports",
        sa.Column(
            "lifecycle_status",
            sa.String(length=32),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.add_column(
        "story_novel_exports",
        sa.Column(
            "continuity_status",
            sa.String(length=32),
            nullable=False,
            server_default="unchecked",
        ),
    )
    op.add_column(
        "story_novel_exports",
        sa.Column(
            "adaptation_plan_status",
            sa.String(length=32),
            nullable=False,
            server_default="empty",
        ),
    )
    for name, column_type in [
        ("content_hash", sa.String(length=64)),
        ("story_snapshot", sa.JSON()),
        ("generation_plan", sa.JSON()),
        ("continuity_ledger", sa.JSON()),
        ("continuity_report", sa.JSON()),
        ("adaptation_plan", sa.JSON()),
        ("approved_at", sa.DateTime(timezone=True)),
        ("approved_by", sa.Integer()),
    ]:
        op.add_column(
            "story_novel_exports", sa.Column(name, column_type, nullable=True)
        )
    if dialect == "sqlite":
        with op.batch_alter_table("story_novel_exports") as batch:
            batch.create_foreign_key(
                "fk_story_novel_exports_approved_by",
                "users",
                ["approved_by"],
                ["id"],
                ondelete="SET NULL",
            )
    else:
        op.create_foreign_key(
            "fk_story_novel_exports_approved_by",
            "story_novel_exports",
            "users",
            ["approved_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "story_novel_chapters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("novel_export_id", sa.Integer(), nullable=False),
        sa.Column("novel_export_business_id", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "content_text",
            sa.Text().with_variant(mysql.LONGTEXT(), "mysql"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("cliffhanger", sa.Text(), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=32),
            nullable=False,
            server_default="ready",
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["novel_export_id"], ["story_novel_exports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(
        "ix_story_novel_chapters_business_id",
        "story_novel_chapters",
        ["business_id"],
    )
    op.create_index(
        "ix_story_novel_chapters_novel_export_id",
        "story_novel_chapters",
        ["novel_export_id"],
    )
    op.create_index(
        "ix_story_novel_chapters_novel_export_business_id",
        "story_novel_chapters",
        ["novel_export_business_id"],
    )

    op.add_column(
        "episodes", sa.Column("source_novel_export_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "episodes",
        sa.Column(
            "source_novel_export_business_id", sa.String(length=32), nullable=True
        ),
    )
    op.add_column(
        "episodes", sa.Column("source_chapter_refs", sa.JSON(), nullable=True)
    )
    op.create_index(
        "ix_episodes_source_novel_export_id",
        "episodes",
        ["source_novel_export_id"],
    )
    op.create_index(
        "ix_episodes_source_novel_export_business_id",
        "episodes",
        ["source_novel_export_business_id"],
    )
    if dialect == "sqlite":
        with op.batch_alter_table("episodes") as batch:
            batch.create_foreign_key(
                "fk_episodes_source_novel_export_id",
                "story_novel_exports",
                ["source_novel_export_id"],
                ["id"],
                ondelete="SET NULL",
            )
        with op.batch_alter_table("stories") as batch:
            batch.create_foreign_key(
                "fk_stories_canonical_novel_export_id",
                "story_novel_exports",
                ["canonical_novel_export_id"],
                ["id"],
                ondelete="SET NULL",
            )
    else:
        op.create_foreign_key(
            "fk_episodes_source_novel_export_id",
            "episodes",
            "story_novel_exports",
            ["source_novel_export_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_stories_canonical_novel_export_id",
            "stories",
            "story_novel_exports",
            ["canonical_novel_export_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        with op.batch_alter_table("stories") as batch:
            batch.drop_constraint(
                "fk_stories_canonical_novel_export_id", type_="foreignkey"
            )
        with op.batch_alter_table("episodes") as batch:
            batch.drop_constraint(
                "fk_episodes_source_novel_export_id", type_="foreignkey"
            )
    else:
        op.drop_constraint(
            "fk_stories_canonical_novel_export_id", "stories", type_="foreignkey"
        )
        op.drop_constraint(
            "fk_episodes_source_novel_export_id", "episodes", type_="foreignkey"
        )
    op.drop_index("ix_episodes_source_novel_export_business_id", table_name="episodes")
    op.drop_index("ix_episodes_source_novel_export_id", table_name="episodes")
    op.drop_column("episodes", "source_chapter_refs")
    op.drop_column("episodes", "source_novel_export_business_id")
    op.drop_column("episodes", "source_novel_export_id")
    op.drop_table("story_novel_chapters")
    if dialect == "sqlite":
        with op.batch_alter_table("story_novel_exports") as batch:
            batch.drop_constraint(
                "fk_story_novel_exports_approved_by", type_="foreignkey"
            )
    else:
        op.drop_constraint(
            "fk_story_novel_exports_approved_by",
            "story_novel_exports",
            type_="foreignkey",
        )
    for name in [
        "approved_by",
        "approved_at",
        "adaptation_plan",
        "continuity_report",
        "continuity_ledger",
        "generation_plan",
        "story_snapshot",
        "content_hash",
        "adaptation_plan_status",
        "continuity_status",
        "lifecycle_status",
        "revision_number",
    ]:
        op.drop_column("story_novel_exports", name)
    op.drop_index("ix_stories_canonical_novel_export_id", table_name="stories")
    op.drop_column("stories", "canonical_novel_export_id")
    op.drop_column("stories", "workflow_mode")
