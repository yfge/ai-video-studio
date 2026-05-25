from copy import deepcopy

import pytest
from app.services.timeline_spec_validation import validate_timeline_spec
from app.services.timeline_spec_validation_types import TimelineSpecValidationError


def _valid_spec() -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": 10,
        "script_id": 20,
        "version": 1,
        "source_audio_timeline_version": 3,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 2400,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    _clip("dialogue_scene_1_beat_1_001", 1, 0, 1200),
                    _clip("dialogue_scene_1_beat_2_002", 2, 1200, 2400),
                ],
            }
        ],
    }


def _clip(clip_id: str, ordinal: int, start_ms: int, end_ms: int) -> dict:
    beat_id = f"beat_{ordinal}"
    return {
        "clip_id": clip_id,
        "track_type": "dialogue",
        "scene_id": "scene_1",
        "beat_id": beat_id,
        "ordinal": ordinal,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": "scene_1",
            "beat_id": beat_id,
            "audio_timeline_version": 3,
        },
        "source_refs": {
            "scene_beat_id": beat_id,
            "audio_timeline_version": 3,
        },
    }


def _expect_code(spec: dict, code: str) -> None:
    with pytest.raises(TimelineSpecValidationError) as exc:
        validate_timeline_spec(
            spec,
            episode_id=10,
            script_id=20,
            expected_version=1,
        )
    assert exc.value.code == code


def test_timeline_spec_validation_accepts_valid_shape():
    validate_timeline_spec(
        _valid_spec(), episode_id=10, script_id=20, expected_version=1
    )


def test_timeline_spec_validation_rejects_malformed_track():
    spec = _valid_spec()
    spec["tracks"][0]["clips"] = {"bad": "shape"}

    _expect_code(spec, "timeline_spec_track_clips_invalid")


def test_timeline_spec_validation_rejects_missing_clip_id():
    spec = _valid_spec()
    del spec["tracks"][0]["clips"][0]["clip_id"]

    _expect_code(spec, "timeline_spec_field_missing")


def test_timeline_spec_validation_rejects_non_monotonic_timing():
    spec = _valid_spec()
    spec["tracks"][0]["clips"][1]["start_ms"] = 100
    spec["tracks"][0]["clips"][1]["end_ms"] = 1300
    spec["tracks"][0]["clips"][1]["duration_ms"] = 1200

    _expect_code(spec, "timeline_spec_clip_timing_non_monotonic")


def test_timeline_spec_validation_rejects_invalid_source_reference():
    spec = deepcopy(_valid_spec())
    spec["tracks"][0]["clips"][0]["source_refs"]["scene_beat_id"] = "wrong"

    _expect_code(spec, "timeline_spec_source_mismatch")
