"""Add script review tasktype

Revision ID: 369390d31ba2
Revises: c9d8e7f6a5b4
Create Date: 2026-01-26 21:28:12.380782

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "369390d31ba2"
down_revision: Union[str, Sequence[str], None] = "c9d8e7f6a5b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TASKTYPE_OLD = (
    "IMAGE_GENERATION",
    "IMAGE_EDIT",
    "IMAGE_ENHANCEMENT",
    "STORY_GENERATION",
    "EPISODE_GENERATION",
    "SCRIPT_GENERATION",
    "DIALOGUE_AUDIO_GENERATION",
    "TIMELINE_GENERATION",
    "TIMELINE_PIPELINE",
    "STORYBOARD_GENERATION",
    "VIDEO_GENERATION",
    "TEXT_GENERATION",
)

TASKTYPE_NEW = TASKTYPE_OLD + ("SCRIPT_REVIEW",)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(
            sa.text("ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'SCRIPT_REVIEW'")
        )
        return

    existing_type = sa.Enum(*TASKTYPE_OLD, name="tasktype")
    new_type = sa.Enum(*TASKTYPE_NEW, name="tasktype")

    if dialect == "sqlite":
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=existing_type,
                type_=new_type,
                existing_nullable=False,
            )
        return

    op.alter_column(
        "tasks",
        "task_type",
        existing_type=existing_type,
        type_=new_type,
        existing_nullable=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL enums cannot drop values safely; keep as-is.
        return

    existing_type = sa.Enum(*TASKTYPE_NEW, name="tasktype")
    old_type = sa.Enum(*TASKTYPE_OLD, name="tasktype")

    if dialect == "sqlite":
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=existing_type,
                type_=old_type,
                existing_nullable=False,
            )
        return

    op.alter_column(
        "tasks",
        "task_type",
        existing_type=existing_type,
        type_=old_type,
        existing_nullable=False,
    )
