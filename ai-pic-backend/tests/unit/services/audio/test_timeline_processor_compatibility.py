from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

from app.services.audio import timeline_processor


def test_utc_now_iso_remains_import_compatible() -> None:
    value = timeline_processor.utc_now_iso()
    assert value.endswith("Z")
    datetime.fromisoformat(value.rstrip("Z"))


def test_episode_beat_compatibility_wrapper_delegates(monkeypatch) -> None:
    expected = ([{"beat_id": 1}], 1234)
    captured: dict = {}

    def fake_builder(*, scenes, beats_by_scene_id):
        captured.update(scenes=scenes, beats_by_scene_id=beats_by_scene_id)
        return expected

    monkeypatch.setattr(
        "app.services.audio.episode_timeline_beats.build_episode_timeline_beats",
        fake_builder,
    )

    scenes = [object()]
    beats_by_scene_id = {1: []}
    assert (
        timeline_processor.build_episode_timeline_beats(
            scenes=scenes,
            beats_by_scene_id=beats_by_scene_id,
        )
        == expected
    )
    assert captured == {
        "scenes": scenes,
        "beats_by_scene_id": beats_by_scene_id,
    }


def test_storyboard_builder_compatibility_wrapper_delegates(monkeypatch) -> None:
    expected = [{"frame_id": "canonical-frame"}]
    captured: dict = {}

    def fake_builder(*, audio_timeline, min_pause_duration_ms):
        captured.update(
            audio_timeline=audio_timeline,
            min_pause_duration_ms=min_pause_duration_ms,
        )
        return expected

    monkeypatch.setattr(
        "app.services.audio.storyboard_from_timeline."
        "build_storyboard_frames_from_audio_timeline",
        fake_builder,
    )

    audio_timeline = {"beats": []}
    assert (
        timeline_processor.build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline,
            min_pause_duration_ms=900,
        )
        == expected
    )
    assert captured == {
        "audio_timeline": audio_timeline,
        "min_pause_duration_ms": 900,
    }


def test_storyboard_generation_compatibility_wrapper_marks_legacy(monkeypatch) -> None:
    expected = {"frames": [], "meta": {"source_role": "legacy"}}
    captured: dict = {}

    def fake_generate(db, **kwargs):
        captured.update(db=db, **kwargs)
        return expected

    monkeypatch.setattr(
        "app.services.audio.storyboard_from_timeline."
        "generate_storyboard_from_episode_audio_timeline",
        fake_generate,
    )

    db = object()
    script = object()
    episode = object()
    assert (
        timeline_processor.generate_storyboard_from_episode_audio_timeline(
            db,
            script=script,
            episode=episode,
            overwrite_existing=True,
            min_pause_duration_ms=900,
        )
        == expected
    )
    assert captured == {
        "db": db,
        "script": script,
        "episode": episode,
        "overwrite_existing": True,
        "min_pause_duration_ms": 900,
        "legacy_support_view": True,
    }


def test_application_code_does_not_import_legacy_timeline_processor() -> None:
    app_root = Path(__file__).resolve().parents[4] / "app"
    violations: list[str] = []
    for path in app_root.rglob("*.py"):
        if path.name == "timeline_processor.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module == "app.services.audio.timeline_processor":
                violations.append(str(path.relative_to(app_root.parent)))
    assert violations == []
