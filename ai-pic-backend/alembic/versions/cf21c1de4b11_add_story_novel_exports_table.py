"""add story novel exports table

Revision ID: cf21c1de4b11
Revises: 2a6b1c0d9f01
Create Date: 2026-01-08 14:58:13.838073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'cf21c1de4b11'
down_revision: Union[str, Sequence[str], None] = '2a6b1c0d9f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "story_novel_exports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("story_business_id", sa.String(length=32), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=32), nullable=False, server_default="zhihu"),
        sa.Column("target_words", sa.Integer(), nullable=False),
        sa.Column("chapter_count", sa.Integer(), nullable=True),
        sa.Column("total_words", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("file_relative_path", sa.String(length=512), nullable=True),
        sa.Column(
            "content_text",
            sa.Text().with_variant(mysql.LONGTEXT(), "mysql"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_story_novel_exports_id"), "story_novel_exports", ["id"])
    op.create_index(
        "ix_story_novel_exports_business_id", "story_novel_exports", ["business_id"]
    )
    op.create_index(
        "ix_story_novel_exports_is_deleted", "story_novel_exports", ["is_deleted"]
    )
    op.create_index(
        "ix_story_novel_exports_story_id", "story_novel_exports", ["story_id"]
    )
    op.create_index(
        "ix_story_novel_exports_story_business_id",
        "story_novel_exports",
        ["story_business_id"],
    )
    op.create_index(
        "ix_story_novel_exports_task_id", "story_novel_exports", ["task_id"]
    )
    op.create_index(
        "ix_story_novel_exports_user_id", "story_novel_exports", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_story_novel_exports_user_id", table_name="story_novel_exports")
    op.drop_index("ix_story_novel_exports_task_id", table_name="story_novel_exports")
    op.drop_index(
        "ix_story_novel_exports_story_business_id", table_name="story_novel_exports"
    )
    op.drop_index("ix_story_novel_exports_story_id", table_name="story_novel_exports")
    op.drop_index(
        "ix_story_novel_exports_is_deleted", table_name="story_novel_exports"
    )
    op.drop_index(
        "ix_story_novel_exports_business_id", table_name="story_novel_exports"
    )
    op.drop_index(op.f("ix_story_novel_exports_id"), table_name="story_novel_exports")
    op.drop_table("story_novel_exports")
