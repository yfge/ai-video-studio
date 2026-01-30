"""Add story_format to stories.

Revision ID: 2a6b1c0d9f01
Revises: fcb18d8c3fab
Create Date: 2026-01-08 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a6b1c0d9f01"
down_revision: Union[str, Sequence[str], None] = "fcb18d8c3fab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "stories",
        sa.Column(
            "story_format",
            sa.String(length=32),
            nullable=False,
            server_default="short_drama",
            comment="故事形态：short_drama/tv_series/film",
        ),
    )
    op.alter_column("stories", "story_format", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("stories", "story_format")
