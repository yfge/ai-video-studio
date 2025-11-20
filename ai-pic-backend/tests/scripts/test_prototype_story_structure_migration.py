from copy import deepcopy

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine

from scripts.prototype_story_structure_migration import (
    DEFAULT_ENVIRONMENT,
    DEFAULT_LOCATION,
    DEFAULT_TIME_OF_DAY,
    SAMPLE_EPISODE,
    SAMPLE_SCRIPT,
    SAMPLE_STORY,
    ProbeResult,
    assemble_payload,
    probe_insert,
)


def test_sample_extraction_includes_original_json_and_no_warnings():
    payload, warnings = assemble_payload(deepcopy(SAMPLE_STORY), deepcopy(SAMPLE_EPISODE), deepcopy(SAMPLE_SCRIPT))

    assert warnings == []
    treatment_metadata = payload["story_treatments"][0]["metadata"]
    assert treatment_metadata["original_json"]["title"] == SAMPLE_STORY["title"]

    first_scene = payload["scenes"][0]
    assert first_scene["metadata"]["original_json"]["scene_number"] == SAMPLE_SCRIPT["scenes"][0]["scene_number"]
    assert first_scene["environment_type"] == SAMPLE_SCRIPT["scenes"][0]["environment"]


def test_defaults_and_warnings_when_scene_fields_missing():
    story = {"id": 1, "title": "Test", "premise": None, "synopsis": None, "theme": None, "target_audience": None}
    episode = {"id": 10, "story_id": 1, "episode_number": 1, "title": "Ep", "plot_points": []}
    script = {
        "id": 100,
        "episode_id": 10,
        "title": "Script",
        "content": "",
        "scenes": [
            {
                "scene_number": "1",
                "description": "Missing env/location/time",
            }
        ],
        "dialogues": [],
        "stage_directions": [],
        "storyboard_plan": [
            {"scene_number": 99, "shot_number": "1"},
        ],
    }

    payload, warnings = assemble_payload(story, episode, script)

    assert any("environment missing" in msg for msg in warnings)
    assert any("location missing" in msg for msg in warnings)
    assert any("time_of_day missing" in msg for msg in warnings)
    assert any("Shot for scene 99 skipped" in msg for msg in warnings)

    scene = payload["scenes"][0]
    assert scene["environment_type"] == DEFAULT_ENVIRONMENT
    assert scene["location"] == DEFAULT_LOCATION
    assert scene["time_of_day"] == DEFAULT_TIME_OF_DAY
    assert payload["shots"] == []


def test_probe_insert_reports_missing_tables():
    engine = create_engine("sqlite:///:memory:")
    payload, _ = assemble_payload(deepcopy(SAMPLE_STORY), deepcopy(SAMPLE_EPISODE), deepcopy(SAMPLE_SCRIPT))

    result = probe_insert(engine, payload)

    assert isinstance(result, ProbeResult)
    assert result.attempted is False
    assert set(result.tables_missing) == {
        "story_treatments",
        "story_step_outlines",
        "scenes",
        "scene_beats",
        "shots",
    }
    assert all(count == 0 for count in result.inserted_counts.values())
    assert result.rolled_back is False
    assert result.error is None

    engine.dispose()


def _bootstrap_schema(engine: sa.Engine) -> None:
    metadata = sa.MetaData()

    stories = sa.Table(
        "stories",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255)),
    )
    episodes = sa.Table(
        "episodes",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("stories.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255)),
    )
    scripts = sa.Table(
        "scripts",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id", ondelete="CASCADE")),
        sa.Column("scenes", sa.JSON, nullable=True),
        sa.Column("dialogues", sa.JSON, nullable=True),
        sa.Column("stage_directions", sa.JSON, nullable=True),
        sa.Column("storyboard_plan", sa.JSON, nullable=True),
    )
    users = sa.Table("users", metadata, sa.Column("id", sa.Integer, primary_key=True))
    images = sa.Table("images", metadata, sa.Column("id", sa.Integer, primary_key=True))

    sa.Table(
        "story_treatments",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("logline", sa.Text),
        sa.Column("theme_summary", sa.Text),
        sa.Column("act_structure", sa.JSON),
        sa.Column("target_audience_notes", sa.Text),
        sa.Column("tone_reference", sa.JSON),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("approved_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("ai_prompt_snapshot", sa.JSON),
        sa.Column("metadata", sa.JSON),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    sa.Table(
        "story_step_outlines",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id", ondelete="SET NULL")),
        sa.Column("story_treatment_id", sa.BigInteger, sa.ForeignKey("story_treatments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("act_label", sa.String(50)),
        sa.Column("beat_title", sa.String(255), nullable=False),
        sa.Column("beat_summary", sa.Text),
        sa.Column("dramatic_question", sa.Text),
        sa.Column("characters_involved", sa.JSON),
        sa.Column("location_hint", sa.String(255)),
        sa.Column("duration_estimate_minutes", sa.Numeric(5, 2)),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    sa.Table(
        "scenes",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("script_id", sa.Integer, sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("story_step_outline_id", sa.BigInteger, sa.ForeignKey("story_step_outlines.id", ondelete="SET NULL")),
        sa.Column("scene_number", sa.String(20), nullable=False),
        sa.Column("slug_line", sa.String(255), nullable=False),
        sa.Column("environment_type", sa.String(32)),
        sa.Column("location", sa.String(255)),
        sa.Column("time_of_day", sa.String(50)),
        sa.Column("summary", sa.Text),
        sa.Column("page_length_eighths", sa.Integer),
        sa.Column("primary_characters", sa.JSON),
        sa.Column("conflict_notes", sa.Text),
        sa.Column("ai_prompt_snapshot", sa.JSON),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    sa.Table(
        "scene_beats",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("scene_id", sa.BigInteger, sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False),
        sa.Column("beat_type", sa.String(32)),
        sa.Column("beat_summary", sa.Text),
        sa.Column("characters_involved", sa.JSON),
        sa.Column("dialogue_excerpt", sa.Text),
        sa.Column("camera_notes", sa.Text),
        sa.Column("duration_seconds", sa.Numeric(6, 2)),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    sa.Table(
        "shots",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("scene_id", sa.BigInteger, sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scene_beat_id", sa.BigInteger, sa.ForeignKey("scene_beats.id", ondelete="SET NULL")),
        sa.Column("shot_number", sa.String(20), nullable=False),
        sa.Column("shot_type", sa.String(50)),
        sa.Column("camera_setup", sa.String(255)),
        sa.Column("camera_movement", sa.String(50)),
        sa.Column("framing", sa.Text),
        sa.Column("focus_subject", sa.String(255)),
        sa.Column("duration_seconds", sa.Numeric(6, 2)),
        sa.Column("storyboard_frame_asset_id", sa.Integer, sa.ForeignKey("images.id", ondelete="SET NULL")),
        sa.Column("lighting_notes", sa.Text),
        sa.Column("audio_notes", sa.Text),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(stories.insert().values(id=101, title="Story"))
        conn.execute(episodes.insert().values(id=501, story_id=101))
        conn.execute(scripts.insert().values(id=3001, episode_id=501))
        conn.execute(users.insert().values(id=1))


def test_probe_insert_succeeds_and_rolls_back():
    engine = create_engine("sqlite:///:memory:")
    _bootstrap_schema(engine)

    payload, _ = assemble_payload(deepcopy(SAMPLE_STORY), deepcopy(SAMPLE_EPISODE), deepcopy(SAMPLE_SCRIPT))
    result = probe_insert(engine, payload)

    assert result.attempted is True
    assert result.tables_missing == []
    assert all(count > 0 for count in result.inserted_counts.values())
    assert result.skipped == []
    assert result.rolled_back is True
    assert result.error is None

    with engine.begin() as conn:
        rows = conn.execute(sa.text("SELECT COUNT(*) FROM story_treatments")).scalar_one()
        assert rows == 0

    engine.dispose()
