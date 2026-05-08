"""add virtual ip environment links

Revision ID: 4c8f2e1d9a70
Revises: 3a9af7b70877
Create Date: 2026-05-07 22:18:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c8f2e1d9a70"
down_revision: Union[str, Sequence[str], None] = "3a9af7b70877"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "virtual_ip_environments",
        sa.Column("id", BIGINT_PK, nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("virtual_ip_id", sa.Integer(), nullable=False),
        sa.Column("virtual_ip_business_id", sa.String(length=32), nullable=True),
        sa.Column("environment_id", BIGINT_PK, nullable=False),
        sa.Column("environment_business_id", sa.String(length=32), nullable=True),
        sa.Column("usage_type", sa.String(length=32), nullable=False, server_default="scene_pool"),
        sa.Column("usage_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["environment_id"], ["environments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["virtual_ip_id"], ["virtual_ips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_virtual_ip_environments_business_id"),
        "virtual_ip_environments",
        ["business_id"],
        unique=True,
    )
    op.create_index(
        "ix_virtual_ip_environments_user_id",
        "virtual_ip_environments",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_virtual_ip_environments_virtual_ip_id",
        "virtual_ip_environments",
        ["virtual_ip_id"],
        unique=False,
    )
    op.create_index(
        "ix_virtual_ip_environments_environment_id",
        "virtual_ip_environments",
        ["environment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_virtual_ip_environments_virtual_ip_business_id"),
        "virtual_ip_environments",
        ["virtual_ip_business_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_virtual_ip_environments_environment_business_id"),
        "virtual_ip_environments",
        ["environment_business_id"],
        unique=False,
    )
    op.create_index(
        "ux_virtual_ip_environments_pair_deleted",
        "virtual_ip_environments",
        ["virtual_ip_id", "environment_id", "is_deleted"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_virtual_ip_environments_pair_deleted",
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        op.f("ix_virtual_ip_environments_environment_business_id"),
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        op.f("ix_virtual_ip_environments_virtual_ip_business_id"),
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        "ix_virtual_ip_environments_environment_id",
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        "ix_virtual_ip_environments_virtual_ip_id",
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        "ix_virtual_ip_environments_user_id",
        table_name="virtual_ip_environments",
    )
    op.drop_index(
        op.f("ix_virtual_ip_environments_business_id"),
        table_name="virtual_ip_environments",
    )
    op.drop_table("virtual_ip_environments")
