"""Extend tasktype enum values

Revision ID: c9d8e7f6a5b4
Revises: g3e4f5d6a7b8
Create Date: 2026-01-26

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d8e7f6a5b4"
down_revision: Union[str, Sequence[str], None] = "g3e4f5d6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TASKTYPE_OLD = (
    "IMAGE_GENERATION",
    "IMAGE_EDIT",
    "IMAGE_ENHANCEMENT",
)

TASKTYPE_NEW = TASKTYPE_OLD + (
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


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for value in TASKTYPE_NEW:
            if value in TASKTYPE_OLD:
                continue
            op.execute(
                sa.text(f"ALTER TYPE tasktype ADD VALUE IF NOT EXISTS '{value}'")
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
