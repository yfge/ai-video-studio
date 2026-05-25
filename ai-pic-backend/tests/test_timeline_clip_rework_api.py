from app.models.script import Episode, Script, Story
from app.models.timeline import MediaAsset
from app.models.user import User
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(
        title="Timeline Rework Story",
        genre="short_drama",
        user_id=user.id,
    )
    episode = Episode(
        story=story,
        episode_number=1,
        title="Pilot",
        duration_minutes=3,
    )
    script = Script(
        episode=episode,
        title="Pilot Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _timeline_spec(episode: Episode, script: Script) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 1200,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    {
                        "clip_id": "dialogue_scene_001_beat_001_001",
                        "track_type": "dialogue",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "ordinal": 1,
                        "start_ms": 0,
                        "end_ms": 1200,
                        "duration_ms": 1200,
                        "source": {
                            "kind": "audio_timeline_beat",
                            "scene_id": "scene_001",
                            "beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                        "source_refs": {
                            "scene_beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                    }
                ],
            }
        ],
    }


def _media_asset(
    db: Session,
    *,
    asset_type: str,
    origin: str,
    file_url: str,
    mime_type: str,
) -> MediaAsset:
    asset = MediaAsset(
        asset_type=asset_type,
        origin=origin,
        file_url=file_url,
        mime_type=mime_type,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def _create_timeline(client, episode: Episode, script: Script, spec: dict) -> dict:
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Rework Timeline",
            "spec": spec,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_timeline_clip_rework_preserves_clip_id_and_replaces_prior_asset(
    client, db_session
):
    episode, script = _bootstrap_episode(db_session)
    original_asset = _media_asset(
        db_session,
        asset_type="audio",
        origin="upload",
        file_url="https://example.com/dialogue-v1.mp3",
        mime_type="audio/mpeg",
    )
    replacement_asset = _media_asset(
        db_session,
        asset_type="audio",
        origin="upload",
        file_url="https://example.com/dialogue-v2.mp3",
        mime_type="audio/mpeg",
    )
    spec = _timeline_spec(episode, script)
    clip_id = spec["tracks"][0]["clips"][0]["clip_id"]
    spec["tracks"][0]["clips"][0]["asset_ref"] = {
        "kind": "episode_audio",
        "media_asset_id": original_asset.id,
    }
    timeline = _create_timeline(client, episode, script, spec)
    lineage_response = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"clip_id": clip_id},
    )
    assert lineage_response.status_code == 200
    original_link = lineage_response.json()["items"][0]

    rework_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework",
        json={
            "expected_version": timeline["version"],
            "action": "re_dub",
            "media_asset_id": replacement_asset.id,
            "reason": "cleaner voice take",
        },
    )

    assert rework_response.status_code == 200
    replacement = rework_response.json()
    assert replacement["clip_id"] == clip_id
    assert replacement["asset_role"] == "source_audio"
    assert replacement["media_asset_id"] == replacement_asset.id
    assert replacement["replacement_of_id"] == original_link["id"]
    assert replacement["source"] == "operator_rework"
    assert replacement["source_ref"]["action"] == "re_dub"
    assert replacement["source_ref"]["preserves_clip_id"] is True


def test_timeline_clip_video_rework_records_recut_and_rerender_roles(
    client, db_session
):
    episode, script = _bootstrap_episode(db_session)
    recut_asset = _media_asset(
        db_session,
        asset_type="video",
        origin="upload",
        file_url="https://example.com/clip-recut-v2.mp4",
        mime_type="video/mp4",
    )
    rerender_asset = _media_asset(
        db_session,
        asset_type="video",
        origin="rendered",
        file_url="https://example.com/clip-render-v2.mp4",
        mime_type="video/mp4",
    )
    timeline = _create_timeline(
        client, episode, script, _timeline_spec(episode, script)
    )
    clip_id = timeline["spec"]["tracks"][0]["clips"][0]["clip_id"]

    recut_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "media_asset_id": recut_asset.id,
        },
    )
    rerender_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework",
        json={
            "expected_version": timeline["version"],
            "action": "re_render",
            "media_asset_id": rerender_asset.id,
        },
    )

    assert recut_response.status_code == 200
    recut = recut_response.json()
    assert recut["clip_id"] == clip_id
    assert recut["asset_role"] == "generated_video"
    assert recut["replacement_of_id"] is None
    assert recut["media_asset"]["file_url"] == "https://example.com/clip-recut-v2.mp4"
    assert rerender_response.status_code == 200
    rerender = rerender_response.json()
    assert rerender["clip_id"] == clip_id
    assert rerender["asset_role"] == "render_output"
    assert rerender["replacement_of_id"] is None
    assert (
        rerender["media_asset"]["file_url"] == "https://example.com/clip-render-v2.mp4"
    )


def test_timeline_clip_rework_rejects_stale_version_and_missing_clip(
    client, db_session
):
    episode, script = _bootstrap_episode(db_session)
    video_asset = _media_asset(
        db_session,
        asset_type="video",
        origin="upload",
        file_url="https://example.com/recut.mp4",
        mime_type="video/mp4",
    )
    timeline = _create_timeline(
        client, episode, script, _timeline_spec(episode, script)
    )
    clip_id = timeline["spec"]["tracks"][0]["clips"][0]["clip_id"]

    stale_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework",
        json={
            "expected_version": timeline["version"] + 1,
            "action": "re_cut",
            "media_asset_id": video_asset.id,
        },
    )
    missing_clip_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/missing_clip/rework",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "media_asset_id": video_asset.id,
        },
    )

    assert stale_response.status_code == 409
    assert missing_clip_response.status_code == 404
