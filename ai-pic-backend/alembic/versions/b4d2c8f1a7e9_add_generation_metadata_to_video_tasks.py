"""Add generation_metadata to video_generation_tasks.

Stores normalized provider/model/task_id/output metadata (mime/sha256/dimensions, etc.)
to reduce provider-specific branching when consuming video generation results.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4d2c8f1a7e9"
down_revision = "a97c737e5d56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "video_generation_tasks",
        sa.Column("generation_metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("video_generation_tasks", "generation_metadata")
