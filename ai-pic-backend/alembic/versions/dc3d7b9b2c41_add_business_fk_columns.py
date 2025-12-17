"""add business_id link columns and backfill"""

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = "dc3d7b9b2c41"
down_revision = "b9b5c7e3a8d1"
branch_labels = None
depends_on = None


def _add_columns():
    op.add_column(
        "episodes",
        sa.Column("story_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_episodes_story_business_id",
        "episodes",
        ["story_business_id"],
    )

    op.add_column(
        "scripts",
        sa.Column("episode_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_scripts_episode_business_id",
        "scripts",
        ["episode_business_id"],
    )

    op.add_column(
        "story_characters",
        sa.Column("story_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "story_characters",
        sa.Column("virtual_ip_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_story_characters_story_business_id",
        "story_characters",
        ["story_business_id"],
    )
    op.create_index(
        "ix_story_characters_virtual_ip_business_id",
        "story_characters",
        ["virtual_ip_business_id"],
    )

    op.add_column(
        "story_step_outlines",
        sa.Column("story_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "story_step_outlines",
        sa.Column("episode_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "story_step_outlines",
        sa.Column("story_treatment_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_story_step_outlines_story_business_id",
        "story_step_outlines",
        ["story_business_id"],
    )
    op.create_index(
        "ix_story_step_outlines_episode_business_id",
        "story_step_outlines",
        ["episode_business_id"],
    )
    op.create_index(
        "ix_story_step_outlines_story_treatment_business_id",
        "story_step_outlines",
        ["story_treatment_business_id"],
    )

    op.add_column(
        "scenes",
        sa.Column("script_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "scenes",
        sa.Column("story_step_outline_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "scenes",
        sa.Column("environment_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_scenes_script_business_id",
        "scenes",
        ["script_business_id"],
    )
    op.create_index(
        "ix_scenes_story_step_outline_business_id",
        "scenes",
        ["story_step_outline_business_id"],
    )
    op.create_index(
        "ix_scenes_environment_business_id",
        "scenes",
        ["environment_business_id"],
    )

    op.add_column(
        "scene_beats",
        sa.Column("scene_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_scene_beats_scene_business_id",
        "scene_beats",
        ["scene_business_id"],
    )

    op.add_column(
        "shots",
        sa.Column("scene_business_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "shots",
        sa.Column("scene_beat_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_shots_scene_business_id",
        "shots",
        ["scene_business_id"],
    )
    op.create_index(
        "ix_shots_scene_beat_business_id",
        "shots",
        ["scene_beat_business_id"],
    )

    op.add_column(
        "virtual_ip_images",
        sa.Column("virtual_ip_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_virtual_ip_images_virtual_ip_business_id",
        "virtual_ip_images",
        ["virtual_ip_business_id"],
    )

    op.add_column(
        "tasks",
        sa.Column("target_business_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_tasks_target_business_id",
        "tasks",
        ["target_business_id"],
    )


def _backfill(bind):
    def _fill_child(child_table, child_pk, child_fk_col, parent_table, parent_pk, parent_biz_col, child_biz_col):
        rows = bind.execute(
            sa.text(
                f"""
                SELECT c.{child_pk}, p.{parent_biz_col}
                FROM {child_table} c
                JOIN {parent_table} p ON c.{child_fk_col} = p.{parent_pk}
                WHERE c.{child_biz_col} IS NULL
                """
            )
        ).fetchall()
        for cid, biz in rows:
            if not biz:
                biz = uuid.uuid4().hex
            bind.execute(
                sa.text(
                    f"UPDATE {child_table} SET {child_biz_col} = :biz WHERE {child_pk} = :cid"
                ),
                {"biz": biz, "cid": cid},
            )

    _fill_child(
        child_table="episodes",
        child_pk="id",
        child_fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _fill_child(
        child_table="scripts",
        child_pk="id",
        child_fk_col="episode_id",
        parent_table="episodes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="episode_business_id",
    )
    _fill_child(
        child_table="story_characters",
        child_pk="id",
        child_fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _fill_child(
        child_table="story_characters",
        child_pk="id",
        child_fk_col="virtual_ip_id",
        parent_table="virtual_ips",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="virtual_ip_business_id",
    )
    _fill_child(
        child_table="story_step_outlines",
        child_pk="id",
        child_fk_col="story_id",
        parent_table="stories",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_business_id",
    )
    _fill_child(
        child_table="story_step_outlines",
        child_pk="id",
        child_fk_col="episode_id",
        parent_table="episodes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="episode_business_id",
    )
    _fill_child(
        child_table="story_step_outlines",
        child_pk="id",
        child_fk_col="story_treatment_id",
        parent_table="story_treatments",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_treatment_business_id",
    )
    _fill_child(
        child_table="scenes",
        child_pk="id",
        child_fk_col="script_id",
        parent_table="scripts",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="script_business_id",
    )
    _fill_child(
        child_table="scenes",
        child_pk="id",
        child_fk_col="story_step_outline_id",
        parent_table="story_step_outlines",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="story_step_outline_business_id",
    )
    _fill_child(
        child_table="scenes",
        child_pk="id",
        child_fk_col="environment_id",
        parent_table="environments",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="environment_business_id",
    )
    _fill_child(
        child_table="scene_beats",
        child_pk="id",
        child_fk_col="scene_id",
        parent_table="scenes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_business_id",
    )
    _fill_child(
        child_table="shots",
        child_pk="id",
        child_fk_col="scene_id",
        parent_table="scenes",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_business_id",
    )
    _fill_child(
        child_table="shots",
        child_pk="id",
        child_fk_col="scene_beat_id",
        parent_table="scene_beats",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="scene_beat_business_id",
    )
    _fill_child(
        child_table="virtual_ip_images",
        child_pk="id",
        child_fk_col="virtual_ip_id",
        parent_table="virtual_ips",
        parent_pk="id",
        parent_biz_col="business_id",
        child_biz_col="virtual_ip_business_id",
    )
    # tasks.target_business_id intentionally left null (set by callers per task target)


def upgrade():
    bind = op.get_bind()
    _add_columns()
    _backfill(bind)


def _drop_index_and_column(table, index_name, column_name):
    op.drop_index(index_name, table_name=table)
    op.drop_column(table, column_name)


def downgrade():
    _drop_index_and_column("tasks", "ix_tasks_target_business_id", "target_business_id")
    _drop_index_and_column(
        "virtual_ip_images",
        "ix_virtual_ip_images_virtual_ip_business_id",
        "virtual_ip_business_id",
    )
    _drop_index_and_column("shots", "ix_shots_scene_beat_business_id", "scene_beat_business_id")
    _drop_index_and_column("shots", "ix_shots_scene_business_id", "scene_business_id")
    _drop_index_and_column("scene_beats", "ix_scene_beats_scene_business_id", "scene_business_id")
    _drop_index_and_column("scenes", "ix_scenes_environment_business_id", "environment_business_id")
    _drop_index_and_column(
        "scenes", "ix_scenes_story_step_outline_business_id", "story_step_outline_business_id"
    )
    _drop_index_and_column("scenes", "ix_scenes_script_business_id", "script_business_id")
    _drop_index_and_column(
        "story_step_outlines",
        "ix_story_step_outlines_story_treatment_business_id",
        "story_treatment_business_id",
    )
    _drop_index_and_column(
        "story_step_outlines",
        "ix_story_step_outlines_episode_business_id",
        "episode_business_id",
    )
    _drop_index_and_column(
        "story_step_outlines",
        "ix_story_step_outlines_story_business_id",
        "story_business_id",
    )
    _drop_index_and_column(
        "story_characters",
        "ix_story_characters_virtual_ip_business_id",
        "virtual_ip_business_id",
    )
    _drop_index_and_column(
        "story_characters", "ix_story_characters_story_business_id", "story_business_id"
    )
    _drop_index_and_column("scripts", "ix_scripts_episode_business_id", "episode_business_id")
    _drop_index_and_column("episodes", "ix_episodes_story_business_id", "story_business_id")
