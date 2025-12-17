"""backfill and validate business_id link columns"""

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = "e7d5f9d2c3b0"
down_revision = "dc3d7b9b2c41"
branch_labels = None
depends_on = None


def _coerce_uuid(value):
    return value if value else uuid.uuid4().hex


def _backfill_business_ids(bind):
    tables = [
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
    for table in tables:
        rows = bind.execute(
            sa.text(f"SELECT id, business_id FROM {table} WHERE business_id IS NULL")
        ).fetchall()
        for row_id, biz in rows:
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET business_id = :biz WHERE id = :row_id"
                ),
                {"biz": _coerce_uuid(biz), "row_id": row_id},
            )


def _backfill_link(
    bind,
    *,
    child_table: str,
    child_pk: str,
    fk_col: str,
    parent_table: str,
    parent_pk: str,
    parent_biz_col: str,
    child_biz_col: str,
):
    rows = bind.execute(
        sa.text(
            f"""
            SELECT c.{child_pk}, p.{parent_biz_col}
            FROM {child_table} c
            JOIN {parent_table} p ON c.{fk_col} = p.{parent_pk}
            WHERE c.{child_biz_col} IS NULL AND c.{fk_col} IS NOT NULL
            """
        )
    ).fetchall()
    for cid, biz in rows:
        bind.execute(
            sa.text(
                f"UPDATE {child_table} SET {child_biz_col} = :biz WHERE {child_pk} = :cid"
            ),
            {"biz": _coerce_uuid(biz), "cid": cid},
        )


def _backfill_links(bind):
    _backfill_link(
        bind,
        child_table="episodes",
        child_pk="id",
        fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _backfill_link(
        bind,
        child_table="scripts",
        child_pk="id",
        fk_col="episode_id",
        parent_table="episodes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="episode_business_id",
    )
    _backfill_link(
        bind,
        child_table="story_characters",
        child_pk="id",
        fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _backfill_link(
        bind,
        child_table="story_characters",
        child_pk="id",
        fk_col="virtual_ip_id",
        parent_table="virtual_ips",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="virtual_ip_business_id",
    )
    _backfill_link(
        bind,
        child_table="story_step_outlines",
        child_pk="id",
        fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _backfill_link(
        bind,
        child_table="story_step_outlines",
        child_pk="id",
        fk_col="episode_id",
        parent_table="episodes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="episode_business_id",
    )
    _backfill_link(
        bind,
        child_table="story_step_outlines",
        child_pk="id",
        fk_col="story_treatment_id",
        parent_table="story_treatments",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_treatment_business_id",
    )
    _backfill_link(
        bind,
        child_table="scenes",
        child_pk="id",
        fk_col="script_id",
        parent_table="scripts",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="script_business_id",
    )
    _backfill_link(
        bind,
        child_table="scenes",
        child_pk="id",
        fk_col="story_step_outline_id",
        parent_table="story_step_outlines",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_step_outline_business_id",
    )
    _backfill_link(
        bind,
        child_table="scenes",
        child_pk="id",
        fk_col="environment_id",
        parent_table="environments",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="environment_business_id",
    )
    _backfill_link(
        bind,
        child_table="scene_beats",
        child_pk="id",
        fk_col="scene_id",
        parent_table="scenes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_business_id",
    )
    _backfill_link(
        bind,
        child_table="shots",
        child_pk="id",
        fk_col="scene_id",
        parent_table="scenes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_business_id",
    )
    _backfill_link(
        bind,
        child_table="shots",
        child_pk="id",
        fk_col="scene_beat_id",
        parent_table="scene_beats",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_beat_business_id",
    )
    _backfill_link(
        bind,
        child_table="virtual_ip_images",
        child_pk="id",
        fk_col="virtual_ip_id",
        parent_table="virtual_ips",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="virtual_ip_business_id",
    )


def upgrade():
    bind = op.get_bind()
    _backfill_business_ids(bind)
    _backfill_links(bind)


def downgrade():
    # data-only migration; no schema changes to revert
    pass
