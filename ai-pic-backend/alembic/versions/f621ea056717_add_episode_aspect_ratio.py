"""add episode aspect ratio

Revision ID: f621ea056717
Revises: e1f2a3b4c5d6
Create Date: 2026-01-29 14:57:04.590752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f621ea056717"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "episodes",
        sa.Column(
            "aspect_ratio",
            sa.String(length=8),
            nullable=True,
            comment="Optional aspect ratio override: 9:16/16:9; inherit story default when NULL.",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("episodes", "aspect_ratio")
