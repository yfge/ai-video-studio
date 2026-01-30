"""restore unique constraints with is_deleted composite

This migration restores unique constraints with is_deleted as part of the
composite key, allowing soft-deleted records to coexist with active records
that have the same business key.

MySQL limitation: We cannot use partial unique indexes (WHERE is_deleted=false),
so we include is_deleted in the unique key. This means:
- One active record (is_deleted=false) and one soft-deleted record (is_deleted=true)
  can have the same business key
- Multiple soft-deleted records with the same key are NOT allowed

For business_id: kept as simple unique since it's globally unique by design.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "g3e4f5d6a7b8"
down_revision = "cf21c1de4b11"
branch_labels = None
depends_on = None


BUSINESS_TABLES = [
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


def _safe_drop_index(table: str, name: str):
    """Drop index if it exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes(table)}
    if name in existing:
        op.drop_index(name, table_name=table)


def _safe_create_index(table: str, name: str, columns: list[str], unique: bool):
    """Create index, dropping existing one with same name first."""
    _safe_drop_index(table, name)
    op.create_index(name, table, columns, unique=unique)


def upgrade():
    # 1. business_id: restore as simple unique (globally unique by design)
    for table in BUSINESS_TABLES:
        idx_name = f"ix_{table}_business_id"
        _safe_create_index(table, idx_name, ["business_id"], unique=True)

    # 2. users: (email, is_deleted) and (username, is_deleted) composite unique
    _safe_create_index(
        "users",
        "ux_users_email_is_deleted",
        ["email", "is_deleted"],
        unique=True,
    )
    _safe_create_index(
        "users",
        "ux_users_username_is_deleted",
        ["username", "is_deleted"],
        unique=True,
    )
    # Keep the old non-unique indexes for query performance
    _safe_create_index("users", op.f("ix_users_email"), ["email"], unique=False)
    _safe_create_index("users", op.f("ix_users_username"), ["username"], unique=False)

    # 3. virtual_ips: (user_id, name, is_deleted) - scoped to user
    _safe_create_index(
        "virtual_ips",
        "ux_virtual_ips_user_name_is_deleted",
        ["user_id", "name", "is_deleted"],
        unique=True,
    )
    # Keep the old non-unique index for query performance
    _safe_create_index(
        "virtual_ips", op.f("ix_virtual_ips_name"), ["name"], unique=False
    )

    # 4. Story structure tables: add is_deleted to composite unique keys
    _safe_create_index(
        "story_treatments",
        "ux_story_treatments_story_revision_deleted",
        ["story_id", "revision_number", "is_deleted"],
        unique=True,
    )
    _safe_create_index(
        "story_step_outlines",
        "ux_step_outlines_treatment_sequence_deleted",
        ["story_treatment_id", "sequence_number", "is_deleted"],
        unique=True,
    )
    _safe_create_index(
        "scenes",
        "ux_scenes_script_scene_deleted",
        ["script_id", "scene_number", "is_deleted"],
        unique=True,
    )
    _safe_create_index(
        "scene_beats",
        "ux_scene_beats_scene_order_deleted",
        ["scene_id", "order_index", "is_deleted"],
        unique=True,
    )
    _safe_create_index(
        "shots",
        "ux_shots_scene_shot_deleted",
        ["scene_id", "shot_number", "is_deleted"],
        unique=True,
    )

    # Drop old non-unique composite indexes (replaced by new ones above)
    _safe_drop_index("story_treatments", "ux_story_treatments_story_revision")
    _safe_drop_index("story_step_outlines", "ux_step_outlines_treatment_sequence")
    _safe_drop_index("scenes", "ux_scenes_script_scene_number")
    _safe_drop_index("scene_beats", "ux_scene_beats_scene_order")
    _safe_drop_index("shots", "ux_shots_scene_shot_number")


def downgrade():
    # Revert business_id to non-unique
    for table in BUSINESS_TABLES:
        idx_name = f"ix_{table}_business_id"
        _safe_create_index(table, idx_name, ["business_id"], unique=False)

    # Drop new composite unique indexes
    _safe_drop_index("users", "ux_users_email_is_deleted")
    _safe_drop_index("users", "ux_users_username_is_deleted")
    _safe_drop_index("virtual_ips", "ux_virtual_ips_user_name_is_deleted")
    _safe_drop_index("story_treatments", "ux_story_treatments_story_revision_deleted")
    _safe_drop_index(
        "story_step_outlines", "ux_step_outlines_treatment_sequence_deleted"
    )
    _safe_drop_index("scenes", "ux_scenes_script_scene_deleted")
    _safe_drop_index("scene_beats", "ux_scene_beats_scene_order_deleted")
    _safe_drop_index("shots", "ux_shots_scene_shot_deleted")

    # Restore old non-unique composite indexes
    _safe_create_index(
        "story_treatments",
        "ux_story_treatments_story_revision",
        ["story_id", "revision_number"],
        unique=False,
    )
    _safe_create_index(
        "story_step_outlines",
        "ux_step_outlines_treatment_sequence",
        ["story_treatment_id", "sequence_number"],
        unique=False,
    )
    _safe_create_index(
        "scenes",
        "ux_scenes_script_scene_number",
        ["script_id", "scene_number"],
        unique=False,
    )
    _safe_create_index(
        "scene_beats",
        "ux_scene_beats_scene_order",
        ["scene_id", "order_index"],
        unique=False,
    )
    _safe_create_index(
        "shots",
        "ux_shots_scene_shot_number",
        ["scene_id", "shot_number"],
        unique=False,
    )
