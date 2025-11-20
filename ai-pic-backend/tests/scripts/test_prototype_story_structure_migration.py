from copy import deepcopy

import pytest
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
