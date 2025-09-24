"""Enhance storyboard metadata structure

Revision ID: 0a4c3f0a6b12
Revises: fe284ccd1b92
Create Date: 2025-02-14 10:45:00.000000

"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a4c3f0a6b12"
down_revision: Union[str, Sequence[str], None] = "fe284ccd1b92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def upgrade() -> None:
    """Upgrade schema and backfill storyboard metadata."""
    op.add_column(
        "scripts",
        sa.Column("storyboard_plan", sa.JSON(), nullable=True, comment="最新分镜规划"),
    )
    op.add_column(
        "scripts",
        sa.Column("storyboard_version", sa.Integer(), nullable=True, server_default="1", comment="分镜版本号"),
    )
    op.add_column(
        "scripts",
        sa.Column("storyboard_updated_at", sa.DateTime(), nullable=True, comment="分镜最近更新时间"),
    )

    connection = op.get_bind()
    scripts = connection.execute(sa.text("SELECT id, extra_metadata FROM scripts WHERE extra_metadata IS NOT NULL"))

    update_stmt = sa.text("UPDATE scripts SET extra_metadata = :extra_meta_json, storyboard_updated_at = :updated_at WHERE id = :id")

    for row in scripts:
        try:
            script_id = row["id"]
            extra_meta = row["extra_metadata"]
        except (TypeError, KeyError):
            script_id, extra_meta = row
        extra = _load_json(extra_meta)
        if not extra:
            continue
        storyboard = extra.get("storyboard") if isinstance(extra, dict) else None
        frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
        if not isinstance(frames, list):
            continue
        changed = False
        now_iso = datetime.utcnow().isoformat()
        for idx, frame in enumerate(frames, start=1):
            if not isinstance(frame, dict):
                continue
            if not frame.get("frame_id"):
                frame["frame_id"] = str(uuid.uuid4())
                changed = True
            if frame.get("scene_index") is None and frame.get("scene_number") is not None:
                frame["scene_index"] = frame.get("scene_number")
                changed = True
            if frame.get("generated_at") is None:
                frame["generated_at"] = now_iso
                changed = True
            if frame.get("updated_at") is None:
                frame["updated_at"] = now_iso
                changed = True
            if frame.get("generation_source") is None:
                frame["generation_source"] = "legacy"
                changed = True
            if frame.get("generation_method") is None:
                frame["generation_method"] = "ai" if frame.get("ai_prompt") else "manual"
                changed = True
            if frame.get("frame_number") is None:
                frame["frame_number"] = idx
                changed = True
        if changed:
            extra["storyboard"] = {"frames": frames}
            connection.execute(
                update_stmt,
                {
                    "id": script_id,
                    "extra_meta_json": json.dumps(extra, ensure_ascii=False),
                    "updated_at": datetime.utcnow(),
                },
            )

    op.alter_column("scripts", "storyboard_version", server_default=None)


def downgrade() -> None:
    """Downgrade schema (metadata backfill is not reversible)."""
    op.drop_column("scripts", "storyboard_updated_at")
    op.drop_column("scripts", "storyboard_version")
    op.drop_column("scripts", "storyboard_plan")
