"""merge heads: storyboard metadata and story structure tables

Revision ID: 7f3d2a1b9c00
Revises: 0a4c3f0a6b12, a1b2c3d4e5f6
Create Date: 2025-10-20 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f3d2a1b9c00"
down_revision: Union[str, Sequence[str], None] = ("0a4c3f0a6b12", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge to unify heads."""
    pass


def downgrade() -> None:
    """No-op; splitting heads is not supported in this merge script."""
    pass

