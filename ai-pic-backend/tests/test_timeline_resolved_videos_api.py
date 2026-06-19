import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import MediaAsset, Timeline, TimelineClipAsset
from app.models.user import User
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Resolved Video Story", genre="short_drama", user_id=user.id)
    episode = Episode(story=story, episode_number=1, title="Pilot")
    script = Script(
        episode=episode,
        title="Pilot Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "timeline_clip_id": "video_storyboard",
                        "video_url": "https://example.com/storyboard.mp4",
                    }
                ]
            }
        },
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _media_asset(db: Session, url: str) -> MediaAsset:
    asset = MediaAsset(
        asset_type="video",
        origin="upload",
        file_url=url,
        mime_type="video/mp4",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def _timeline_spec(episode: Episode, script: Script, original_asset: MediaAsset):
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 7000,
        "tracks": [
            {
                "track_type": "video",
                "clips": [
                    _video_clip(
                        "video_generated",
                        asset_ref={
                            "kind": "generated_video",
                            "media_asset_id": original_asset.id,
                        },
                    ),
                    _video_clip(
                        "video_direct",
                        video_url="https://example.com/direct.mp4",
                        start_ms=1000,
                        end_ms=2000,
                    ),
                    _video_clip("video_storyboard", start_ms=2000, end_ms=3000),
                    _video_clip("video_generating", start_ms=3000, end_ms=4000),
                    _video_clip("video_missing", start_ms=4000, end_ms=7000),
                ],
            }
        ],
    }


def _video_clip(
    clip_id: str,
    *,
    start_ms: int = 0,
    end_ms: int = 1000,
    video_url: str | None = None,
    asset_ref: dict | None = None,
):
    clip = {
        "clip_id": clip_id,
        "track_type": "video",
        "scene_id": "scene_001",
        "scene_number": 1,
        "beat_id": "beat_001",
        "ordinal": 1,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": "scene_001",
            "beat_id": "beat_001",
            "audio_timeline_version": 1,
        },
        "text": clip_id,
    }
    if video_url:
        clip["video_url"] = video_url
    if asset_ref:
        clip["asset_ref"] = asset_ref
    return clip


def test_resolved_videos_prioritizes_lineage_and_marks_generating(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    original_asset = _media_asset(db_session, "https://example.com/original.mp4")
    replacement_asset = _media_asset(db_session, "https://example.com/replacement.mp4")

    create_response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Resolved Video Timeline",
            "spec": _timeline_spec(episode, script, original_asset),
        },
    )
    assert create_response.status_code == 200, create_response.text
    timeline = create_response.json()
    direct_link = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.timeline_id == timeline["id"])
        .filter(TimelineClipAsset.clip_id == "video_direct")
        .first()
    )
    assert direct_link is not None
    direct_link.is_deleted = True
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline["id"],
            timeline_version=timeline["version"],
            clip_id="video_generated",
            track_type="video",
            asset_role="generated_video",
            media_asset_id=replacement_asset.id,
            source="provider_rework",
            source_ref={"preserves_clip_id": True},
            created_by=user.id,
        )
    )
    db_session.add(
        Task(
            target_business_id=timeline["business_id"],
            title="Timeline clip video - video_generating",
            task_type=TaskType.VIDEO_GENERATION,
            status=TaskStatus.PROCESSING,
            parameters=json.dumps({"clip_id": "video_generating"}),
            user_id=user.id,
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/timelines/{timeline['id']}/resolved-videos")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["timeline_id"] == timeline["id"]
    assert payload["timeline_version"] == timeline["version"]
    assert payload["video_clip_count"] == 5
    assert payload["missing_clip_count"] == 1
    assert payload["generating_clip_count"] == 1
    assert payload["ready"] is False
    items = {item["clip_id"]: item for item in payload["items"]}
    assert items["video_generated"]["status"] == "ready"
    assert items["video_generated"]["url"] == "https://example.com/replacement.mp4"
    assert items["video_generated"]["source"] == "timeline_clip_asset:provider_rework"
    assert items["video_direct"]["url"] == "https://example.com/direct.mp4"
    assert items["video_direct"]["source"] == "timeline_clip"
    assert items["video_storyboard"]["url"] == "https://example.com/storyboard.mp4"
    assert items["video_storyboard"]["source"] == "storyboard_frame"
    assert items["video_generating"]["status"] == "generating"
    assert items["video_generating"]["reason"] == "generating"
    assert items["video_generating"]["task_type"] == "video_generation"
    assert items["video_missing"]["status"] == "missing"
    assert items["video_missing"]["reason"] == "missing_video_url"


def test_resolved_videos_fills_short_missing_clip_from_neighbor(
    client,
    db_session,
):
    episode, script = _bootstrap_episode(db_session)
    original_asset = _media_asset(db_session, "https://example.com/original.mp4")
    spec = _timeline_spec(episode, script, original_asset)
    spec["duration_ms"] = 2500
    spec["tracks"][0]["clips"] = [
        _video_clip(
            "video_ready_before",
            video_url="https://example.com/before.mp4",
            start_ms=0,
            end_ms=1000,
        ),
        _video_clip("video_short_gap", start_ms=1000, end_ms=1800),
        _video_clip(
            "video_ready_after",
            video_url="https://example.com/after.mp4",
            start_ms=1800,
            end_ms=2500,
        ),
    ]

    create_response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Resolved Short Gap Timeline",
            "spec": spec,
        },
    )
    assert create_response.status_code == 200, create_response.text
    timeline = create_response.json()

    response = client.get(f"/api/v1/timelines/{timeline['id']}/resolved-videos")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ready"] is True
    assert payload["missing_clip_count"] == 0
    items = {item["clip_id"]: item for item in payload["items"]}
    assert items["video_short_gap"]["status"] == "ready"
    assert items["video_short_gap"]["url"] == "https://example.com/before.mp4"
    assert items["video_short_gap"]["source"] == (
        "short_gap_neighbor:video_ready_before"
    )


def test_resolved_videos_keeps_generated_assets_after_timeline_version_bump(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    original_asset = _media_asset(db_session, "https://example.com/original.mp4")
    generated_asset = _media_asset(db_session, "https://example.com/generated.mp4")
    spec = _timeline_spec(episode, script, original_asset)
    spec["tracks"][0]["clips"] = [
        _video_clip("video_generated", start_ms=0, end_ms=1000)
    ]

    create_response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Version Bump Resolved Timeline",
            "spec": spec,
        },
    )
    assert create_response.status_code == 200, create_response.text
    timeline = create_response.json()
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline["id"],
            timeline_version=timeline["version"],
            clip_id="video_generated",
            track_type="video",
            asset_role="generated_video",
            media_asset_id=generated_asset.id,
            source="provider_rework",
            created_by=user.id,
        )
    )
    db_session.query(Timeline).filter(Timeline.id == timeline["id"]).update(
        {Timeline.version: timeline["version"] + 1}
    )
    db_session.commit()

    response = client.get(f"/api/v1/timelines/{timeline['id']}/resolved-videos")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ready"] is True
    items = {item["clip_id"]: item for item in payload["items"]}
    assert items["video_generated"]["url"] == "https://example.com/generated.mp4"
    assert items["video_generated"]["source"] == "timeline_clip_asset:provider_rework"
