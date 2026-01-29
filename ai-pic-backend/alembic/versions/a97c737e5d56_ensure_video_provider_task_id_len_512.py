"""Ensure video_generation_tasks.provider_task_id length is at least 512.

Vertex operation names (and some provider task IDs) can exceed the historical 128-char limit.
This migration is defensive: it inspects the current column length and only alters when needed.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a97c737e5d56"
down_revision = "f621ea056717"
branch_labels = None
depends_on = None


def _get_current_length(conn) -> int | None:
    try:
        result = conn.execute(
            sa.text(
                """
                SELECT CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'video_generation_tasks'
                  AND COLUMN_NAME = 'provider_task_id'
                """
            )
        ).scalar()
        return int(result) if result is not None else None
    except Exception:  # noqa: BLE001 - best-effort schema introspection
        return None


def upgrade() -> None:
    conn = op.get_bind()
    current_len = _get_current_length(conn)
    if current_len is not None and current_len >= 512:
        return

    op.alter_column(
        "video_generation_tasks",
        "provider_task_id",
        existing_type=sa.String(length=current_len or 128),
        type_=sa.String(length=512),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "video_generation_tasks",
        "provider_task_id",
        existing_type=sa.String(length=512),
        type_=sa.String(length=128),
        existing_nullable=False,
    )

