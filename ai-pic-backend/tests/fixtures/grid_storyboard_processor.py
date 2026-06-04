import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_grid_storyboard_panels,
)
from app.services.timeline_revision_service import TimelineRevisionService
from sqlalchemy.orm import Session


def bootstrap_episode(db: Session) -> tuple[User, Episode, Script]:
    user = User(
        username="grid_processor_admin",
        email="grid_processor_admin@example.com",
        hashed_password="test",
        is_active=True,
        is_superuser=True,
        is_admin=True,
        is_approved=True,
        email_verified=True,
    )
    story = Story(title="Grid Storyboard Story", genre="short_drama", user_id=user.id)
    episode = Episode(story=story, episode_number=1, title="Pilot")
    script = Script(
        episode=episode,
        title="Pilot Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([user, story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return user, episode, script


def timeline_spec(episode: Episode, script: Script) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 2400,
        "tracks": [],
    }


def append_video_clips(spec: dict) -> dict:
    spec["tracks"].append(
        {
            "track_type": "video",
            "clips": [
                video_clip("video_scene_001_beat_001_001", "beat_001", 0, 1200),
                video_clip("video_scene_001_beat_002_001", "beat_002", 1200, 2400),
            ],
        }
    )
    return spec


def video_clip(clip_id: str, beat_id: str, start_ms: int, end_ms: int) -> dict:
    return {
        "clip_id": clip_id,
        "track_type": "video",
        "scene_id": "scene_001",
        "beat_id": beat_id,
        "ordinal": 1 if beat_id == "beat_001" else 2,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": "scene_001",
            "beat_id": beat_id,
            "audio_timeline_version": 1,
        },
        "source_refs": {"scene_beat_id": beat_id},
        "text": "A rainy close-up of the lead character.",
    }


def create_timeline(
    db: Session,
    episode: Episode,
    script: Script,
    spec: dict,
    user: User,
) -> Timeline:
    timeline = Timeline(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        script_id=script.id,
        script_business_id=script.business_id,
        title="Grid Storyboard Timeline",
        status="draft",
        spec=spec,
        version=1,
        source_audio_timeline_version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(timeline)
    db.flush()
    timeline.spec = TimelineRevisionService(db).spec_with_identity(timeline)
    db.commit()
    db.refresh(timeline)
    return timeline


def create_grid_task(db: Session, timeline: Timeline, user: User) -> Task:
    task = Task(
        target_business_id=timeline.business_id,
        title="Grid storyboard",
        description="Grid storyboard generation",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="sheet prompt",
        parameters=json.dumps({}, ensure_ascii=False),
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def bump_timeline_version_without_panel_changes(
    db: Session,
    timeline: Timeline,
    user: User,
) -> None:
    revisions = TimelineRevisionService(db)
    revisions.ensure_revision(
        timeline,
        reason="pre_update_snapshot",
        user_id=user.id,
    )
    timeline.status = "review"
    timeline.version = 2
    timeline.spec = revisions.spec_with_identity(timeline)
    revisions.ensure_revision(timeline, reason="updated", user_id=user.id)
    db.commit()
    db.refresh(timeline)


def change_timeline_panel_prompt(
    db: Session,
    timeline: Timeline,
    user: User,
) -> None:
    revisions = TimelineRevisionService(db)
    revisions.ensure_revision(
        timeline,
        reason="pre_update_snapshot",
        user_id=user.id,
    )
    spec = dict(timeline.spec)
    tracks = [dict(track) for track in spec["tracks"]]
    clips = [dict(clip) for clip in tracks[0]["clips"]]
    clips[0] = {**clips[0], "text": "A changed prompt for the first grid panel."}
    tracks[0] = {**tracks[0], "clips": clips}
    timeline.spec = {**spec, "tracks": tracks}
    timeline.version = 2
    timeline.spec = revisions.spec_with_identity(timeline)
    revisions.ensure_revision(timeline, reason="updated", user_id=user.id)
    db.commit()
    db.refresh(timeline)


async def fake_image_generator(**kwargs):
    assert kwargs["prompt"] == "sheet prompt"
    return {
        "urls": ["https://provider.example/grid.png"],
        "provider": "fake",
        "model": "fake-image",
        "image_gen": {"prompt_sha256": "abc123"},
    }


async def fake_image_persister(**kwargs):
    assert kwargs["image_data"] == "https://provider.example/grid.png"
    return {
        "oss_url": "https://cdn.example/grid.png",
        "local_file_path": "/tmp/grid.png",
        "relative_path": "uploads/grid.png",
    }


def processor_payload(timeline: Timeline) -> dict:
    panels = build_grid_storyboard_panels(timeline.spec, panel_count=4)
    return {
        "kind": "timeline_storyboard_grid",
        "timeline_id": timeline.id,
        "timeline_version": timeline.version,
        "expected_version": timeline.version,
        "panel_count": 4,
        "columns": 2,
        "rows": 2,
        "style": "3d_cartoon",
        "model": "fake-image",
        "generation_profile": "storyboard_grid",
        "size": "1536x1536",
        "aspect_ratio": "1:1",
        "panels": panels,
        "sheet_prompt": "sheet prompt",
    }
