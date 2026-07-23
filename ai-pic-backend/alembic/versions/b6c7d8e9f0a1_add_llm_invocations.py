"""Add complete per-attempt LLM invocation records.

Revision ID: b6c7d8e9f0a1
Revises: a8b9c0d1e2f3
Create Date: 2026-07-23 16:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LONG_TEXT = sa.Text().with_variant(mysql.LONGTEXT(), "mysql")


def upgrade() -> None:
    op.create_table(
        "llm_invocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "invocation_type",
            sa.String(32),
            nullable=False,
            server_default="text",
        ),
        sa.Column("call_scene", sa.String(512), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(255)),
        sa.Column("attempt_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(24), nullable=False, server_default="processing"),
        sa.Column("original_prompt", LONG_TEXT, nullable=False),
        sa.Column("prompt", LONG_TEXT, nullable=False),
        sa.Column("system_prompt", LONG_TEXT),
        sa.Column("response", LONG_TEXT),
        sa.Column("error", LONG_TEXT),
        sa.Column("request_parameters", sa.JSON()),
        sa.Column("input_references", sa.JSON()),
        sa.Column("output_assets", sa.JSON()),
        sa.Column("usage", sa.JSON()),
        sa.Column("response_metadata", sa.JSON()),
        sa.Column("provider_task_id", sa.String(512)),
        sa.Column("input_tokens", sa.BigInteger()),
        sa.Column("cache_tokens", sa.BigInteger()),
        sa.Column("output_tokens", sa.BigInteger()),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "invocation_type",
        "call_scene",
        "provider",
        "model",
        "status",
        "provider_task_id",
        "started_at",
    ):
        op.create_index(f"ix_llm_invocations_{column}", "llm_invocations", [column])
    with op.batch_alter_table("video_generation_tasks") as batch:
        batch.add_column(sa.Column("llm_invocation_id", sa.Integer(), nullable=True))
        batch.create_index(
            "ix_video_generation_tasks_llm_invocation_id",
            ["llm_invocation_id"],
        )
        batch.create_foreign_key(
            "fk_video_generation_tasks_llm_invocation_id",
            "llm_invocations",
            ["llm_invocation_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("video_generation_tasks") as batch:
        batch.drop_constraint(
            "fk_video_generation_tasks_llm_invocation_id",
            type_="foreignkey",
        )
        batch.drop_index("ix_video_generation_tasks_llm_invocation_id")
        batch.drop_column("llm_invocation_id")
    op.drop_table("llm_invocations")
