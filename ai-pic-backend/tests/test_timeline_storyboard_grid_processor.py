import anyio
import pytest

from app.models.task import TaskStatus
from app.models.timeline import MediaAsset, TimelineClipAsset
from app.services.storyboard.grid_storyboard_sheet_processor import (
    GridStoryboardSheetProcessor,
)
from tests.fixtures.grid_storyboard_processor import (
    append_video_clips,
    bootstrap_episode,
    bump_timeline_version_without_panel_changes,
    change_timeline_panel_prompt,
    create_grid_task,
    create_timeline,
    fake_image_generator,
    fake_image_persister,
    processor_payload,
    timeline_spec,
)


def test_grid_storyboard_processor_persists_sheet_and_support_view(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    task = create_grid_task(db_session, timeline, user)

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=fake_image_generator,
        image_persister=fake_image_persister,
    )
    anyio.run(
        processor.process_grid_sheet_task,
        task.id,
        processor_payload(timeline),
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


def test_grid_storyboard_processor_rebases_when_current_panels_still_match(
    db_session,
):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    payload = processor_payload(timeline)
    bump_timeline_version_without_panel_changes(db_session, timeline, user)
    task = create_grid_task(db_session, timeline, user)

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=fake_image_generator,
        image_persister=fake_image_persister,
    )
    anyio.run(processor.process_grid_sheet_task, task.id, payload, user.id)

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert timeline.version == 3
    grid = timeline.spec["support_views"]["storyboard_grid"]
    assert grid["source_timeline_version"] == 1
    assert grid["sheet"]["file_url"] == "https://cdn.example/grid.png"
    video_clips = timeline.spec["tracks"][0]["clips"]
    assert video_clips[0]["source_refs"]["grid_storyboard_panel"]["panel_index"] == 1


def test_grid_storyboard_processor_rejects_rebase_when_panel_snapshot_changed(
    db_session,
):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    payload = processor_payload(timeline)
    change_timeline_panel_prompt(db_session, timeline, user)
    task = create_grid_task(db_session, timeline, user)

    async def unexpected_image_generator(**kwargs):
        raise AssertionError("image generation should not run for stale panels")

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=unexpected_image_generator,
        image_persister=fake_image_persister,
    )

    with pytest.raises(RuntimeError, match="timeline version conflict"):
        anyio.run(processor.process_grid_sheet_task, task.id, payload, user.id)

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.FAILED
    assert "support_views" not in timeline.spec
