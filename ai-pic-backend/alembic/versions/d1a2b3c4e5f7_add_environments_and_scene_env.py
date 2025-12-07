"""add environments table and scene environment relation

Revision ID: d1a2b3c4e5f7
Revises: 7f3d2a1b9c00
Create Date: 2025-12-07 16:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4e5f7"
down_revision: Union[str, None] = "c4a1cbf0d7c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "environments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_images", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "scenes",
        sa.Column("environment_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_scenes_environment_id",
        "scenes",
        "environments",
        ["environment_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_scenes_environment_id", "scenes", type_="foreignkey")
    op.drop_column("scenes", "environment_id")
    op.drop_table("environments")
