"""Add user ownership to core content assets

Revision ID: f3c2d1e4a5b6
Revises: e2f4c6d8b9aa
Create Date: 2025-12-11 01:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3c2d1e4a5b6"
down_revision: Union[str, Sequence[str], None] = "e2f4c6d8b9aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_id foreign keys to virtual_ips, stories and environments, and backfill existing rows."""
    # virtual_ips.user_id
    op.add_column(
        "virtual_ips",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_virtual_ips_user_id",
        "virtual_ips",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_virtual_ips_user_id",
        "virtual_ips",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # stories.user_id
    op.add_column(
        "stories",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_stories_user_id",
        "stories",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_stories_user_id",
        "stories",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # environments.user_id
    op.add_column(
        "environments",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_environments_user_id",
        "environments",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_environments_user_id",
        "environments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill existing rows: assign ownership to the earliest user (typically the first admin)
    conn = op.get_bind()
    try:
        result = conn.execute(sa.text("SELECT MIN(id) FROM users"))
        first_user_id = result.scalar()
    except Exception:
        first_user_id = None

    if first_user_id is not None:
        conn.execute(
            sa.text(
                "UPDATE virtual_ips SET user_id = :uid WHERE user_id IS NULL"
            ),
            {"uid": first_user_id},
        )
        conn.execute(
            sa.text(
                "UPDATE stories SET user_id = :uid WHERE user_id IS NULL"
            ),
            {"uid": first_user_id},
        )
        conn.execute(
            sa.text(
                "UPDATE environments SET user_id = :uid WHERE user_id IS NULL"
            ),
            {"uid": first_user_id},
        )


def downgrade() -> None:
    """Drop user_id ownership columns and constraints."""
    # environments
    op.drop_constraint("fk_environments_user_id", "environments", type_="foreignkey")
    op.drop_index("ix_environments_user_id", table_name="environments")
    op.drop_column("environments", "user_id")

    # stories
    op.drop_constraint("fk_stories_user_id", "stories", type_="foreignkey")
    op.drop_index("ix_stories_user_id", table_name="stories")
    op.drop_column("stories", "user_id")

    # virtual_ips
    op.drop_constraint("fk_virtual_ips_user_id", "virtual_ips", type_="foreignkey")
    op.drop_index("ix_virtual_ips_user_id", table_name="virtual_ips")
    op.drop_column("virtual_ips", "user_id")

