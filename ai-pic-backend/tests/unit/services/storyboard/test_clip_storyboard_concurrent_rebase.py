import anyio
import pytest
from app.models.task import TaskStatus
from app.services.storyboard.grid_storyboard_sheet_payload import clip_source_signature
from app.services.storyboard.grid_storyboard_sheet_processor import (
    GridStoryboardSheetProcessor,
)
from tests.fixtures.grid_storyboard_processor import (
    append_video_clips,
    bootstrap_episode,
    create_grid_task,
    create_timeline,
    fake_image_generator,
    fake_image_persister,
    timeline_spec,
)


def test_different_clip_storyboards_rebase_from_same_source_version(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    first_id = "video_scene_001_beat_001_001"
    second_id = "video_scene_001_beat_002_001"
    first_payload = _payload(timeline, first_id)
    second_payload = _payload(timeline, second_id)
    first_task = create_grid_task(db_session, timeline, user)
    second_task = create_grid_task(db_session, timeline, user)
    processor = _processor(db_session)

    anyio.run(
        processor.process_grid_sheet_task,
        first_task.id,
        first_payload,
        user.id,
    )
    anyio.run(
        processor.process_grid_sheet_task,
        second_task.id,
        second_payload,
        user.id,
    )

    db_session.refresh(timeline)
    db_session.refresh(second_task)
    assert second_task.status == TaskStatus.COMPLETED
    assert timeline.version == 3
    assert set(timeline.spec["support_views"]["clip_storyboards"]) == {
        first_id,
        second_id,
    }


def test_same_clip_storyboard_rebase_rejects_concurrent_overwrite(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    clip_id = "video_scene_001_beat_001_001"
    first_payload = _payload(timeline, clip_id)
    second_payload = _payload(timeline, clip_id)
    first_task = create_grid_task(db_session, timeline, user)
    second_task = create_grid_task(db_session, timeline, user)
    processor = _processor(db_session)

    anyio.run(
        processor.process_grid_sheet_task,
        first_task.id,
        first_payload,
        user.id,
    )
    with pytest.raises(RuntimeError, match="timeline version conflict"):
        anyio.run(
            processor.process_grid_sheet_task,
            second_task.id,
            second_payload,
            user.id,
        )

    db_session.refresh(second_task)
    assert second_task.status == TaskStatus.FAILED


def test_clip_storyboard_locks_timeline_from_fresh_transaction(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    clip_id = "video_scene_001_beat_001_001"
    task = create_grid_task(db_session, timeline, user)
    processor = _processor(db_session)
    original_get_for_update = processor.timelines.get_by_id_for_update
    transaction_states = []

    def get_for_update(timeline_id):
        transaction_states.append(db_session.in_transaction())
        return original_get_for_update(timeline_id)

    processor.timelines.get_by_id_for_update = get_for_update
    anyio.run(
        processor.process_grid_sheet_task,
        task.id,
        _payload(timeline, clip_id),
        user.id,
    )

    assert transaction_states == [False]


def _processor(db_session):
    return GridStoryboardSheetProcessor(
        db_session,
        image_generator=fake_image_generator,
        image_persister=fake_image_persister,
    )


def _payload(timeline, clip_id: str) -> dict:
    clip = next(
        clip
        for track in timeline.spec["tracks"]
        for clip in track.get("clips") or []
        if clip.get("clip_id") == clip_id
    )
    return {
        "kind": "timeline_clip_storyboard",
        "timeline_id": timeline.id,
        "timeline_version": timeline.version,
        "expected_version": timeline.version,
        "clip_id": clip_id,
        "clip_source_signature": clip_source_signature(clip),
        "panel_count": 2,
        "columns": 2,
        "rows": 1,
        "style": "3d_cartoon",
        "model": "fake-image",
        "panels": [
            {
                "panel_index": index,
                "clip_id": clip_id,
                "visual_prompt": f"Moment {index}",
            }
            for index in (1, 2)
        ],
        "sheet_prompt": "sheet prompt",
    }
