from app.models.script import Episode, Script, Story
from app.models.timeline import Timeline

from scripts.backfill_timeline_specs import backfill_timeline_specs


def _create_episode_with_audio_timeline(db_session, *, script_match: bool = True):
    story = Story(title="Backfill Story", genre="drama", user_id=1)
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")
    db_session.add_all([story, episode, script])
    db_session.commit()
    db_session.refresh(episode)
    db_session.refresh(script)

    timeline_script_id = script.id if script_match else script.id + 1000
    episode.extra_metadata = {
        "audio_timeline": {
            "script_id": timeline_script_id,
            "episode_audio": {
                "oss_url": "https://cdn.example.com/backfill.mp3",
                "duration_seconds": 1.2,
                "version": 12,
            },
            "beats": [
                {
                    "scene_id": 10,
                    "scene_number": 1,
                    "beat_id": 20,
                    "beat_type": "dialogue",
                    "text": "hello",
                    "start_ms": 0,
                    "end_ms": 1200,
                }
            ],
        }
    }
    db_session.commit()
    db_session.refresh(episode)
    return episode, script


def test_backfill_timeline_specs_dry_run_does_not_write(db_session):
    _create_episode_with_audio_timeline(db_session)

    counters = backfill_timeline_specs(db_session, apply=False)

    assert counters["scanned"] == 1
    assert counters["would_create"] == 1
    assert db_session.query(Timeline).count() == 0


def test_backfill_timeline_specs_apply_creates_timeline(db_session):
    episode, script = _create_episode_with_audio_timeline(db_session)

    counters = backfill_timeline_specs(db_session, apply=True)

    assert counters["created"] == 1
    timeline = db_session.query(Timeline).one()
    assert timeline.episode_id == episode.id
    assert timeline.script_id == script.id
    assert timeline.source_audio_timeline_version == 12
    assert timeline.spec["timeline_id"] == timeline.id


def test_backfill_timeline_specs_counts_script_mismatch(db_session):
    _create_episode_with_audio_timeline(db_session, script_match=False)

    counters = backfill_timeline_specs(db_session, apply=True)

    assert counters["script_mismatch"] == 1
    assert counters["created"] == 0
