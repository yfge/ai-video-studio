"""add business_id and soft delete fields to core tables"""

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = "b9b5c7e3a8d1"
down_revision = "c4a1cbf0d7c2"
branch_labels = None
depends_on = None

TABLES = [
    "users",
    "user_audit_logs",
    "images",
    "virtual_ips",
    "virtual_ip_images",
    "stories",
    "episodes",
    "scripts",
    "story_characters",
    "script_templates",
    "tasks",
    "story_treatments",
    "story_step_outlines",
    "scenes",
    "scene_beats",
    "shots",
    "environments",
]


def _add_columns_and_indexes(default_expr):
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "business_id",
                sa.String(length=32),
                nullable=True,
                server_default=default_expr,
            ),
        )
        op.add_column(
            table,
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.add_column(
            table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
        )
        op.add_column(table, sa.Column("deleted_by", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("deleted_reason", sa.Text(), nullable=True))
        op.create_index(
            f"ix_{table}_business_id", table, ["business_id"], unique=True
        )
        op.create_index(f"ix_{table}_is_deleted", table, ["is_deleted"])


def _backfill_business_ids(bind):
    for table in TABLES:
        rows = bind.execute(
            sa.text(f"SELECT id FROM {table} WHERE business_id IS NULL")
        ).fetchall()
        for (row_id,) in rows:
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET business_id = :bid WHERE id = :row_id"
                ),
                {"bid": uuid.uuid4().hex, "row_id": row_id},
            )


def _enforce_not_null():
    for table in TABLES:
        op.alter_column(
            table,
            "business_id",
            existing_type=sa.String(length=32),
            nullable=False,
        )


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    default_expr = sa.text("replace(uuid(), '-', '')") if dialect == "mysql" else None

    _add_columns_and_indexes(default_expr)
    _backfill_business_ids(bind)
    _enforce_not_null()


def downgrade():
    for table in TABLES:
        op.drop_index(f"ix_{table}_business_id", table_name=table)
        op.drop_index(f"ix_{table}_is_deleted", table_name=table)
        op.drop_column(table, "deleted_reason")
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "is_deleted")
        op.drop_column(table, "business_id")
