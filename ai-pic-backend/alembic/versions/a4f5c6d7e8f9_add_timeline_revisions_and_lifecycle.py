"""add timeline revisions and lifecycle state

Revision ID: a4f5c6d7e8f9
Revises: 8d1b6e2a4f90
Create Date: 2026-05-25 12:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4f5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "8d1b6e2a4f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    with op.batch_alter_table("timelines") as batch_op:
        batch_op.add_column(
            sa.Column("rollback_of_version", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("rollback_target_version", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("rolled_back_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_timelines_rolled_back_by_users",
            "users",
            ["rolled_back_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "timeline_revisions",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("timeline_id", BIGINT_PK, nullable=False),
        sa.Column("timeline_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("source_audio_timeline_version", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timeline_revisions_timeline_id",
        "timeline_revisions",
        ["timeline_id"],
        unique=False,
    )
    op.create_index(
        "ux_timeline_revisions_timeline_version",
        "timeline_revisions",
        ["timeline_id", "timeline_version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_timeline_revisions_timeline_version", table_name="timeline_revisions"
    )
    op.drop_index("ix_timeline_revisions_timeline_id", table_name="timeline_revisions")
    op.drop_table("timeline_revisions")
    with op.batch_alter_table("timelines") as batch_op:
        batch_op.drop_constraint(
            "fk_timelines_rolled_back_by_users", type_="foreignkey"
        )
        batch_op.drop_column("rolled_back_by")
        batch_op.drop_column("rolled_back_at")
        batch_op.drop_column("rollback_target_version")
        batch_op.drop_column("rollback_of_version")
