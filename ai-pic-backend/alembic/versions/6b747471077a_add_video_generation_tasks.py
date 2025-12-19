"""add video generation tasks table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6b747471077a"
down_revision = "b7f9e6d3c2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_enum = sa.Enum(
        "pending",
        "submitted",
        "processing",
        "succeeded",
        "failed",
        "timeout",
        name="video_generation_task_status",
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "video_generation_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.String(length=32), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_reason", sa.Text(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("script_id", sa.Integer(), nullable=True),
        sa.Column("frame_index", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_task_id", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("model_type", sa.String(length=32), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("parameters", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_video_generation_tasks_business_id",
        "video_generation_tasks",
        ["business_id"],
    )
    op.create_index(
        "ix_video_generation_tasks_task_id",
        "video_generation_tasks",
        ["task_id"],
    )
    op.create_index(
        "ix_video_generation_tasks_script_id",
        "video_generation_tasks",
        ["script_id"],
    )
    op.create_index(
        "ix_video_generation_tasks_frame_index",
        "video_generation_tasks",
        ["frame_index"],
    )
    op.create_index(
        "ix_video_generation_tasks_provider_task_id",
        "video_generation_tasks",
        ["provider_task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_video_generation_tasks_provider_task_id", table_name="video_generation_tasks")
    op.drop_index("ix_video_generation_tasks_frame_index", table_name="video_generation_tasks")
    op.drop_index("ix_video_generation_tasks_script_id", table_name="video_generation_tasks")
    op.drop_index("ix_video_generation_tasks_task_id", table_name="video_generation_tasks")
    op.drop_index("ix_video_generation_tasks_business_id", table_name="video_generation_tasks")
    op.drop_table("video_generation_tasks")

    status_enum = sa.Enum(
        "pending",
        "submitted",
        "processing",
        "succeeded",
        "failed",
        "timeout",
        name="video_generation_task_status",
    )
    status_enum.drop(op.get_bind(), checkfirst=True)
