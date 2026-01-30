"""expand video provider task id length"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c1a2b3c4d5e"
down_revision = "b7f9e6d3c2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "video_generation_tasks",
        "provider_task_id",
        existing_type=sa.String(length=128),
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
