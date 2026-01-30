"""add character_ids to shots

Revision ID: e2f4c6d8b9aa
Revises: d1a2b3c4e5f7
Create Date: 2025-12-07 17:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f4c6d8b9aa"
down_revision: Union[str, None] = "d1a2b3c4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shots",
        sa.Column("character_ids", sa.JSON(), nullable=True, comment="参与角色ID列表"),
    )


def downgrade() -> None:
    op.drop_column("shots", "character_ids")
