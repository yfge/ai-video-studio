"""add timeline main chain tables

Revision ID: 8d1b6e2a4f90
Revises: 4c8f2e1d9a70
Create Date: 2026-05-12 14:25:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8d1b6e2a4f90"
down_revision: Union[str, Sequence[str], None] = "4c8f2e1d9a70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("object_key", sa.String(length=512), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("hash", sa.String(length=128), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_media_assets_business_id"),
        "media_assets",
        ["business_id"],
        unique=True,
    )
    op.create_index(
        "ix_media_assets_asset_type", "media_assets", ["asset_type"], unique=False
    )
    op.create_index("ix_media_assets_origin", "media_assets", ["origin"], unique=False)
    op.create_index("ix_media_assets_hash", "media_assets", ["hash"], unique=False)
    op.create_index(
        "ix_media_assets_created_by", "media_assets", ["created_by"], unique=False
    )

    op.create_table(
        "timelines",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("episode_business_id", sa.String(length=32), nullable=True),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("script_business_id", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="draft"
        ),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_audio_timeline_version", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_timelines_business_id"), "timelines", ["business_id"], unique=True
    )
    op.create_index(
        "ix_timelines_episode_id", "timelines", ["episode_id"], unique=False
    )
    op.create_index(
        "ix_timelines_episode_business_id",
        "timelines",
        ["episode_business_id"],
        unique=False,
    )
    op.create_index("ix_timelines_script_id", "timelines", ["script_id"], unique=False)
    op.create_index(
        "ix_timelines_script_business_id",
        "timelines",
        ["script_business_id"],
        unique=False,
    )
    op.create_index("ix_timelines_status", "timelines", ["status"], unique=False)

    op.create_table(
        "render_jobs",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("timeline_id", BIGINT_PK, nullable=False),
        sa.Column("timeline_version", sa.Integer(), nullable=False),
        sa.Column("render_type", sa.String(length=32), nullable=False),
        sa.Column("preset_hash", sa.String(length=64), nullable=False),
        sa.Column("preset", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="queued"
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_asset_id", BIGINT_PK, nullable=True),
        sa.Column("log", sa.JSON(), nullable=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["output_asset_id"], ["media_assets.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_render_jobs_business_id"), "render_jobs", ["business_id"], unique=True
    )
    op.create_index("ix_render_jobs_status", "render_jobs", ["status"], unique=False)
    op.create_index(
        "ix_render_jobs_created_by", "render_jobs", ["created_by"], unique=False
    )
    op.create_index(
        "ux_render_jobs_idempotency",
        "render_jobs",
        ["timeline_id", "timeline_version", "render_type", "preset_hash", "is_deleted"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_render_jobs_idempotency", table_name="render_jobs")
    op.drop_index("ix_render_jobs_created_by", table_name="render_jobs")
    op.drop_index("ix_render_jobs_status", table_name="render_jobs")
    op.drop_index(op.f("ix_render_jobs_business_id"), table_name="render_jobs")
    op.drop_table("render_jobs")

    op.drop_index("ix_timelines_status", table_name="timelines")
    op.drop_index("ix_timelines_script_business_id", table_name="timelines")
    op.drop_index("ix_timelines_script_id", table_name="timelines")
    op.drop_index("ix_timelines_episode_business_id", table_name="timelines")
    op.drop_index("ix_timelines_episode_id", table_name="timelines")
    op.drop_index(op.f("ix_timelines_business_id"), table_name="timelines")
    op.drop_table("timelines")

    op.drop_index("ix_media_assets_created_by", table_name="media_assets")
    op.drop_index("ix_media_assets_hash", table_name="media_assets")
    op.drop_index("ix_media_assets_origin", table_name="media_assets")
    op.drop_index("ix_media_assets_asset_type", table_name="media_assets")
    op.drop_index(op.f("ix_media_assets_business_id"), table_name="media_assets")
    op.drop_table("media_assets")
