from __future__ import annotations

from unittest.mock import MagicMock

from app.services.audio.episode_timeline_beats import build_episode_timeline_beats


def _scene(scene_id: int, scene_number: object) -> MagicMock:
    scene = MagicMock()
    scene.id = scene_id
    scene.scene_number = scene_number
    return scene


def _beat(
    beat_id: int,
    *,
    beat_type: str,
    duration_seconds: float,
    metadata: dict | None = None,
) -> MagicMock:
    beat = MagicMock()
    beat.id = beat_id
    beat.beat_type = beat_type
    beat.dialogue_excerpt = "Hello"
    beat.beat_summary = "Action summary"
    beat.duration_seconds = duration_seconds
    beat.extra_metadata = metadata or {}
    beat.characters_involved = ["林晚"]
    return beat


def test_build_episode_timeline_beats_offsets_scenes() -> None:
    first = _beat(10, beat_type="dialogue", duration_seconds=2.0)
    second = _beat(20, beat_type="action", duration_seconds=1.0)

    merged, total_ms = build_episode_timeline_beats(
        scenes=[_scene(1, "1"), _scene(2, "2")],
        beats_by_scene_id={1: [first], 2: [second]},
    )

    assert [(item["start_ms"], item["end_ms"]) for item in merged] == [
        (0, 2000),
        (2000, 3000),
    ]
    assert total_ms == 3000


def test_build_episode_timeline_beats_preserves_structured_context() -> None:
    beat = _beat(
        10,
        beat_type="dialogue",
        duration_seconds=0,
        metadata={
            "start_ms": 500,
            "end_ms": 1500,
            "speaker_name": "林晚",
            "action": "抬头",
            "emotion": "紧张",
        },
    )

    merged, total_ms = build_episode_timeline_beats(
        scenes=[_scene(1, "1")],
        beats_by_scene_id={1: [beat]},
    )

    assert merged[0] == {
        "scene_id": 1,
        "scene_number": 1,
        "beat_id": 10,
        "beat_type": "dialogue",
        "speaker_name": "林晚",
        "characters_involved": ["林晚"],
        "dialogue_action": "抬头",
        "dialogue_emotion": "紧张",
        "text": "Hello",
        "start_ms": 500,
        "end_ms": 1500,
    }
    assert total_ms == 1500


def test_build_episode_timeline_beats_clamps_invalid_window() -> None:
    beat = _beat(
        10,
        beat_type="action",
        duration_seconds=1.0,
        metadata={"start_ms": 1500, "end_ms": 500},
    )

    merged, total_ms = build_episode_timeline_beats(
        scenes=[_scene(1, "invalid")],
        beats_by_scene_id={1: [beat]},
    )

    assert merged[0]["scene_number"] is None
    assert merged[0]["text"] == "Action summary"
    assert merged[0]["start_ms"] == merged[0]["end_ms"] == 1500
    assert total_ms == 1500


def test_build_episode_timeline_beats_handles_empty_scenes() -> None:
    assert build_episode_timeline_beats(scenes=[], beats_by_scene_id={}) == ([], 0)
