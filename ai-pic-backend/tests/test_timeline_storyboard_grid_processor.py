import json

import anyio

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import MediaAsset, Timeline, TimelineClipAsset
from app.models.user import User
from app.services.storyboard.grid_storyboard_sheet_processor import (
    GridStoryboardSheetProcessor,
)
from app.services.timeline_revision_service import TimelineRevisionService
from sqlalchemy.orm import Session


def test_grid_storyboard_processor_persists_sheet_and_support_view(db_session):
    user, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        db_session,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
        user,
    )
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
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

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

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=fake_image_generator,
        image_persister=fake_image_persister,
    )
    anyio.run(
        processor.process_grid_sheet_task,
        task.id,
        _processor_payload(timeline),
        user.id,
    )

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert timeline.version == 2
    grid = timeline.spec["support_views"]["storyboard_grid"]
    assert grid["mode"] == "grid_storyboard.v1"
    assert grid["sheet"]["file_url"] == "https://cdn.example/grid.png"
    assert grid["sheet"]["panel_count"] == 4
    video_clips = timeline.spec["tracks"][0]["clips"]
    assert video_clips[0]["source_refs"]["grid_storyboard_panel"]["panel_index"] == 1
    assert video_clips[0]["storyboard_grid_sheet_asset_ref"]["file_url"] == (
        "https://cdn.example/grid.png"
    )
    asset = db_session.query(MediaAsset).filter_by(asset_type="image").one()
    assert asset.origin == "generated"
    links = (
        db_session.query(TimelineClipAsset)
        .filter_by(asset_role="storyboard_grid_sheet")
        .order_by(TimelineClipAsset.clip_id)
        .all()
    )
    assert [link.clip_id for link in links] == [
        "video_scene_001_beat_001_001",
        "video_scene_001_beat_002_001",
    ]


def _bootstrap_episode(db: Session) -> tuple[User, Episode, Script]:
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


def _timeline_spec(episode: Episode, script: Script) -> dict:
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


def _append_video_clips(spec: dict) -> dict:
    spec["tracks"].append(
        {
            "track_type": "video",
            "clips": [
                _video_clip("video_scene_001_beat_001_001", "beat_001", 0, 1200),
                _video_clip("video_scene_001_beat_002_001", "beat_002", 1200, 2400),
            ],
        }
    )
    return spec


def _video_clip(clip_id: str, beat_id: str, start_ms: int, end_ms: int) -> dict:
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


def _create_timeline(
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


def _processor_payload(timeline: Timeline) -> dict:
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
        "panels": [
            {
                "panel_id": "grid_panel_001",
                "panel_index": 1,
                "clip_id": "video_scene_001_beat_001_001",
                "visual_prompt": "林晚站在雨夜门口，霓虹反光，中景",
                "video_prompt": "镜头缓慢推近，雨水落在她肩头",
            },
            {
                "panel_id": "grid_panel_002",
                "panel_index": 2,
                "clip_id": "video_scene_001_beat_002_001",
                "visual_prompt": "陈哲坐在车内，侧脸被手机屏照亮。",
                "video_prompt": "陈哲坐在车内，侧脸被手机屏照亮。",
            },
        ],
        "sheet_prompt": "sheet prompt",
    }
