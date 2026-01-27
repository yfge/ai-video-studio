"""Add task cancelled status

Revision ID: b1b863e84acc
Revises: 369390d31ba2
Create Date: 2026-01-27 21:01:29.645576

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1b863e84acc"
down_revision: Union[str, Sequence[str], None] = "369390d31ba2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TASKSTATUS_OLD = (
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
)

TASKSTATUS_NEW = TASKSTATUS_OLD + ("CANCELLED",)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(sa.text("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'CANCELLED'"))
        return

    existing_type = sa.Enum(*TASKSTATUS_OLD, name="taskstatus")
    new_type = sa.Enum(*TASKSTATUS_NEW, name="taskstatus")

    if dialect == "sqlite":
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.alter_column(
                "status",
                existing_type=existing_type,
                type_=new_type,
                existing_nullable=True,
            )
        return

    op.alter_column(
        "tasks",
        "status",
        existing_type=existing_type,
        type_=new_type,
        existing_nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL enums cannot drop values safely; keep as-is.
        return

    existing_type = sa.Enum(*TASKSTATUS_NEW, name="taskstatus")
    old_type = sa.Enum(*TASKSTATUS_OLD, name="taskstatus")

    if dialect == "sqlite":
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.alter_column(
                "status",
                existing_type=existing_type,
                type_=old_type,
                existing_nullable=True,
            )
        return

    op.alter_column(
        "tasks",
        "status",
        existing_type=existing_type,
        type_=old_type,
        existing_nullable=True,
    )
