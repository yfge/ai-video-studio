"""add timeline clip assets

Revision ID: c5e6f7a8b9c0
Revises: a4f5c6d7e8f9
Create Date: 2026-05-25 13:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "a4f5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "timeline_clip_assets",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("timeline_id", BIGINT_PK, nullable=False),
        sa.Column("timeline_version", sa.Integer(), nullable=False),
        sa.Column("clip_id", sa.String(length=128), nullable=False),
        sa.Column("track_type", sa.String(length=32), nullable=True),
        sa.Column("asset_role", sa.String(length=64), nullable=False),
        sa.Column("media_asset_id", BIGINT_PK, nullable=False),
        sa.Column("render_job_id", BIGINT_PK, nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("source_ref", sa.JSON(), nullable=True),
        sa.Column("replacement_of_id", BIGINT_PK, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["media_asset_id"], ["media_assets.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["render_job_id"], ["render_jobs.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["replacement_of_id"],
            ["timeline_clip_assets.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_timeline_clip_assets_business_id"),
        "timeline_clip_assets",
        ["business_id"],
        unique=True,
    )
    op.create_index(
        "ix_timeline_clip_assets_timeline",
        "timeline_clip_assets",
        ["timeline_id", "timeline_version"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_clip_assets_clip_id",
        "timeline_clip_assets",
        ["clip_id"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_clip_assets_media_asset_id",
        "timeline_clip_assets",
        ["media_asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_clip_assets_asset_role",
        "timeline_clip_assets",
        ["asset_role"],
        unique=False,
    )
    op.create_index(
        "ux_timeline_clip_assets_active",
        "timeline_clip_assets",
        [
            "timeline_id",
            "timeline_version",
            "clip_id",
            "asset_role",
            "media_asset_id",
            "is_deleted",
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_timeline_clip_assets_active", table_name="timeline_clip_assets")
    op.drop_index(
        "ix_timeline_clip_assets_asset_role", table_name="timeline_clip_assets"
    )
    op.drop_index(
        "ix_timeline_clip_assets_media_asset_id", table_name="timeline_clip_assets"
    )
    op.drop_index("ix_timeline_clip_assets_clip_id", table_name="timeline_clip_assets")
    op.drop_index("ix_timeline_clip_assets_timeline", table_name="timeline_clip_assets")
    op.drop_index(
        op.f("ix_timeline_clip_assets_business_id"),
        table_name="timeline_clip_assets",
    )
    op.drop_table("timeline_clip_assets")
