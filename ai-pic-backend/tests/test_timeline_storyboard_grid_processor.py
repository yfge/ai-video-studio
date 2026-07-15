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


def test_clip_storyboard_processor_persists_sheet_for_selected_clip_only(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    task = create_grid_task(db_session, timeline, user)
    selected_clip_id = "video_scene_001_beat_002_001"

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=fake_image_generator,
        image_persister=fake_image_persister,
    )
    anyio.run(
        processor.process_grid_sheet_task,
        task.id,
        _clip_storyboard_payload(timeline, selected_clip_id),
        user.id,
    )

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert timeline.version == 2
    clip_storyboards = timeline.spec["support_views"]["clip_storyboards"]
    assert set(clip_storyboards) == {selected_clip_id}
    storyboard = clip_storyboards[selected_clip_id]
    assert storyboard["mode"] == "clip_storyboard.v1"
    assert storyboard["sheet"]["asset_role"] == "clip_storyboard_sheet"
    assert storyboard["sheet"]["clip_id"] == selected_clip_id
    assert storyboard["sheet"]["file_url"] == "https://cdn.example/grid.png"
    assert {panel["clip_id"] for panel in storyboard["panels"]} == {selected_clip_id}

    video_clips = timeline.spec["tracks"][0]["clips"]
    first_clip, second_clip = video_clips
    assert "clip_storyboard" not in first_clip["source_refs"]
    assert "clip_storyboard_sheet_asset_ref" not in first_clip
    assert second_clip["source_refs"]["clip_storyboard"]["panel_count"] == 4
    assert second_clip["clip_storyboard_sheet_asset_ref"]["file_url"] == (
        "https://cdn.example/grid.png"
    )

    links = (
        db_session.query(TimelineClipAsset)
        .filter_by(asset_role="clip_storyboard_sheet")
        .order_by(TimelineClipAsset.clip_id)
        .all()
    )
    assert [link.clip_id for link in links] == [selected_clip_id]


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


def test_clip_storyboard_processor_does_not_resurrect_cancelled_task(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    task = create_grid_task(db_session, timeline, user)
    selected_clip_id = "video_scene_001_beat_002_001"

    async def image_generator_cancelled_after_provider_return(**kwargs):
        task.status = TaskStatus.CANCELLED
        task.error_message = "cancelled during generation"
        db_session.commit()
        return await fake_image_generator(**kwargs)

    async def unexpected_image_persister(**kwargs):
        raise AssertionError("cancelled task must not persist an image")

    processor = GridStoryboardSheetProcessor(
        db_session,
        image_generator=image_generator_cancelled_after_provider_return,
        image_persister=unexpected_image_persister,
    )
    anyio.run(
        processor.process_grid_sheet_task,
        task.id,
        _clip_storyboard_payload(timeline, selected_clip_id),
        user.id,
    )

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.CANCELLED
    assert timeline.version == 1
    assert "support_views" not in timeline.spec
    assert db_session.query(MediaAsset).count() == 0


def _clip_storyboard_payload(timeline, clip_id: str) -> dict:
    return {
        "kind": "timeline_clip_storyboard",
        "timeline_id": timeline.id,
        "timeline_version": timeline.version,
        "expected_version": timeline.version,
        "clip_id": clip_id,
        "panel_count": 4,
        "columns": 2,
        "rows": 2,
        "style": "3d_cartoon",
        "model": "fake-image",
        "generation_profile": "clip_storyboard",
        "size": "1536x1536",
        "aspect_ratio": "1:1",
        "panels": [
            {
                "panel_id": f"clip_storyboard_panel_{index:03d}",
                "panel_index": index,
                "row": 1 if index <= 2 else 2,
                "column": 1 if index in (1, 3) else 2,
                "clip_id": clip_id,
                "start_ms": 1200,
                "end_ms": 2400,
                "duration_ms": 1200,
                "visual_prompt": f"Selected clip key moment {index}",
                "video_prompt": f"Selected clip motion {index}",
                "storyboard_panel_prompt": f"Panel {index} for selected clip",
            }
            for index in range(1, 5)
        ],
        "sheet_prompt": "sheet prompt",
    }
