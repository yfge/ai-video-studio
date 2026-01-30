"""Expand tasks.parameters to LONGTEXT (MySQL)

Revision ID: 8848b61e51a8
Revises: 39e7d91e9b93
Create Date: 2026-01-28 11:19:53.650219

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "8848b61e51a8"
down_revision: Union[str, Sequence[str], None] = "39e7d91e9b93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    # On MySQL, TEXT is capped at 64KB and can overflow once we store agent_run
    # audit data into Task.parameters for large historical tasks.
    #
    # PostgreSQL TEXT is unbounded; SQLite uses dynamic typing for TEXT.
    if dialect != "mysql":
        return

    op.alter_column(
        "tasks",
        "parameters",
        existing_type=mysql.TEXT(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect != "mysql":
        return

    op.alter_column(
        "tasks",
        "parameters",
        existing_type=mysql.LONGTEXT(),
        type_=mysql.TEXT(),
        existing_nullable=True,
    )
