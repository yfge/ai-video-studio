"""Expand episode generation prompt to LONGTEXT on MySQL.

Revision ID: d4e5f6a7b8c9
Revises: c5e6f7a8b9c0
Create Date: 2026-06-23 20:38:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name != "mysql":
        return

    op.alter_column(
        "episodes",
        "generation_prompt",
        existing_type=mysql.TEXT(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
        existing_comment="生成提示词",
    )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name != "mysql":
        return

    op.alter_column(
        "episodes",
        "generation_prompt",
        existing_type=mysql.LONGTEXT(),
        type_=mysql.TEXT(),
        existing_nullable=True,
        existing_comment="生成提示词",
    )
