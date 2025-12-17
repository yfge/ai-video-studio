"""drop unique constraints in favor of non-unique indexes"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f2d1a3c4b5e6"
down_revision = "e7d5f9d2c3b0"
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


def _recreate_index(table: str, name: str, columns: list[str], unique: bool):
    """Ensure we always have an index for FK columns before dropping unique ones (MySQL)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes(table)}

    # For MySQL FK safety: create a temporary non-unique index before dropping the unique one.
    temp_name = f"{name}_nonuniq_tmp"
    if name in existing and temp_name not in existing and bind.dialect.name == "mysql":
        op.create_index(temp_name, table, columns, unique=False)

    if name in existing:
        op.drop_index(name, table_name=table)
    op.create_index(name, table, columns, unique=unique)

    # Clean up temp index if we created one and replaced original name.
    if temp_name in {idx["name"] for idx in inspector.get_indexes(table)} and name != temp_name:
        try:
            op.drop_index(temp_name, table_name=table)
        except Exception:
            # If drop fails, leave temp index; it is non-unique and harmless.
            pass


def upgrade():
    # Business ID indexes: drop unique and recreate non-unique
    for table in BUSINESS_TABLES:
        idx_name = f"ix_{table}_business_id"
        _recreate_index(table, idx_name, ["business_id"], unique=False)

    # Core fields previously unique
    _recreate_index("users", op.f("ix_users_email"), ["email"], unique=False)
    _recreate_index("users", op.f("ix_users_username"), ["username"], unique=False)
    _recreate_index("virtual_ips", op.f("ix_virtual_ips_name"), ["name"], unique=False)

    # Story structure uniqueness -> non-unique indexes
    # FK-backed indexes: ensure non-unique replacements while keeping FK index coverage.
    _recreate_index(
        "story_treatments",
        "ux_story_treatments_story_revision",
        ["story_id", "revision_number"],
        unique=False,
    )
    _recreate_index(
        "story_step_outlines",
        "ux_step_outlines_treatment_sequence",
        ["story_treatment_id", "sequence_number"],
        unique=False,
    )
    _recreate_index(
        "scenes",
        "ux_scenes_script_scene_number",
        ["script_id", "scene_number"],
        unique=False,
    )
    _recreate_index(
        "scene_beats",
        "ux_scene_beats_scene_order",
        ["scene_id", "order_index"],
        unique=False,
    )
    _recreate_index(
        "shots",
        "ux_shots_scene_shot_number",
        ["scene_id", "shot_number"],
        unique=False,
    )


def downgrade():
    # Restore uniqueness if needed
    for table in BUSINESS_TABLES:
        idx_name = f"ix_{table}_business_id"
        _recreate_index(table, idx_name, ["business_id"], unique=True)

    _recreate_index("users", op.f("ix_users_email"), ["email"], unique=True)
    _recreate_index("users", op.f("ix_users_username"), ["username"], unique=True)
    _recreate_index("virtual_ips", op.f("ix_virtual_ips_name"), ["name"], unique=True)

    _recreate_index(
        "story_treatments",
        "ux_story_treatments_story_revision",
        ["story_id", "revision_number"],
        unique=True,
    )
    _recreate_index(
        "story_step_outlines",
        "ux_step_outlines_treatment_sequence",
        ["story_treatment_id", "sequence_number"],
        unique=True,
    )
    _recreate_index(
        "scenes",
        "ux_scenes_script_scene_number",
        ["script_id", "scene_number"],
        unique=True,
    )
    _recreate_index(
        "scene_beats",
        "ux_scene_beats_scene_order",
        ["scene_id", "order_index"],
        unique=True,
    )
    _recreate_index(
        "shots",
        "ux_shots_scene_shot_number",
        ["scene_id", "shot_number"],
        unique=True,
    )
