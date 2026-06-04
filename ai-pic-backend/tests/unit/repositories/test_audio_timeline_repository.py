from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene, SceneBeat
from app.repositories.audio_timeline_repository import (
    count_scene_beats,
    list_scene_beats,
    list_script_scenes,
)
from app.services.audio.scene_audio_persistence import persist_beats


def test_audio_timeline_repository_ignores_soft_deleted_rows(db_session):
    story = Story(title="Story", genre="test", theme="t", target_audience="all")
    episode = Episode(title="Episode", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    scene = Scene(script=script, scene_number="1", slug_line="INT. TEST - DAY")
    deleted_scene = Scene(script=script, scene_number="2", slug_line="INT. OLD - DAY")
    deleted_scene.soft_delete(reason="test")
    active = SceneBeat(
        scene=scene,
        order_index=1,
        beat_type="dialogue",
        dialogue_excerpt="hello",
        duration_seconds=1,
        extra_metadata={"start_ms": 0, "end_ms": 1000},
    )
    stale_duplicate = SceneBeat(
        scene=scene,
        order_index=1,
        beat_type="dialogue",
        dialogue_excerpt="old hello",
        duration_seconds=1,
        extra_metadata={"start_ms": 0, "end_ms": 1000},
    )
    stale_duplicate.soft_delete(reason="dialogue_audio_overwrite")
    db_session.add_all([story, episode, script, scene, deleted_scene, active, stale_duplicate])
    db_session.commit()

    assert [item.id for item in list_script_scenes(db_session, script.id)] == [scene.id]
    assert [item.id for item in list_scene_beats(db_session, [scene.id])] == [active.id]
    assert count_scene_beats(db_session, scene.id) == 1


def test_persist_beats_overwrite_prunes_existing_soft_deleted_duplicates(db_session):
    story = Story(title="Story", genre="test", theme="t", target_audience="all")
    episode = Episode(title="Episode", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    scene = Scene(script=script, scene_number="1", slug_line="INT. TEST - DAY")
    active = SceneBeat(
        scene=scene,
        order_index=1,
        beat_type="dialogue",
        dialogue_excerpt="current",
        duration_seconds=1,
        extra_metadata={"start_ms": 0, "end_ms": 1000},
    )
    stale_deleted = SceneBeat(
        scene=scene,
        order_index=1,
        beat_type="dialogue",
        dialogue_excerpt="stale",
        duration_seconds=1,
        extra_metadata={"start_ms": 0, "end_ms": 1000},
    )
    stale_deleted.soft_delete(reason="previous_overwrite")
    db_session.add_all([story, episode, script, scene, active, stale_deleted])
    db_session.commit()

    persist_beats(
        db_session,
        [{"beat_type": "dialogue", "dialogue_excerpt": "new", "duration_ms": 1200}],
        scene,
        ["角色"],
        overwrite_beats=True,
    )
    db_session.commit()

    active_beats = list_scene_beats(db_session, [scene.id])
    assert [beat.dialogue_excerpt for beat in active_beats] == ["new"]
    assert active_beats[0].extra_metadata["end_ms"] == 1200
