"""Add voice_config to virtual_ips

Revision ID: 1c2d3e4f5a67
Revises: f3c2d1e4a5b6
Create Date: 2025-12-15 08:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c2d3e4f5a67"
down_revision: Union[str, Sequence[str], None] = "f3c2d1e4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "virtual_ips",
        sa.Column("voice_config", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("virtual_ips", "voice_config")
