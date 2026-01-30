"""Add default_aspect_ratio to stories.

Revision ID: e1f2a3b4c5d6
Revises: 8848b61e51a8, 9c1a2b3c4d5e
Create Date: 2026-01-28 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = ("8848b61e51a8", "9c1a2b3c4d5e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "stories",
        sa.Column(
            "default_aspect_ratio",
            sa.String(length=8),
            nullable=False,
            server_default="9:16",
            comment="默认画幅：9:16/16:9",
        ),
    )
    op.alter_column("stories", "default_aspect_ratio", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("stories", "default_aspect_ratio")
