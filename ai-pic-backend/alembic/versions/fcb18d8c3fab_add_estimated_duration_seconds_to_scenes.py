"""add_estimated_duration_seconds_to_scenes

Revision ID: fcb18d8c3fab
Revises: 6b747471077a
Create Date: 2025-12-25 18:24:57.478014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcb18d8c3fab'
down_revision: Union[str, Sequence[str], None] = '6b747471077a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "scenes",
        sa.Column(
            "estimated_duration_seconds",
            sa.Integer(),
            nullable=True,
            comment="预估场景时长（秒），由LLM生成或手动设置",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("scenes", "estimated_duration_seconds")
