import anyio
from app.models.task import TaskStatus
from app.models.timeline import TimelineClipAsset
from app.services.timeline_clip_keyframe_processor import TimelineClipKeyframeProcessor
from tests.fixtures.grid_storyboard_processor import (
    append_video_clips,
    bootstrap_episode,
    create_grid_task,
    create_timeline,
    timeline_spec,
)


def test_timeline_clip_keyframe_processor_persists_start_and_end_frames(db_session):
    user, episode, script = bootstrap_episode(db_session)
    timeline = create_timeline(
        db_session,
        episode,
        script,
        append_video_clips(timeline_spec(episode, script)),
        user,
    )
    task = create_grid_task(db_session, timeline, user)
    payload = _keyframe_payload(timeline, "video_scene_001_beat_002_001")

    processor = TimelineClipKeyframeProcessor(
        db_session,
        image_generator=_fake_keyframe_generator,
        image_persister=_fake_keyframe_persister,
    )
    anyio.run(processor.process_keyframe_task, task.id, payload, user.id)

    db_session.refresh(timeline)
    db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert timeline.version == 2
    clip = timeline.spec["tracks"][0]["clips"][1]
    assert clip["start_frame_asset_ref"]["file_url"] == (
        "https://cdn.example/start-frame.png"
    )
    assert clip["end_frame_asset_ref"]["file_url"] == (
        "https://cdn.example/end-frame.png"
    )
    keyframes = timeline.spec["support_views"]["clip_keyframes"]
    assert set(keyframes) == {"video_scene_001_beat_002_001"}

    links = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.asset_role.in_(["start_frame", "end_frame"]))
        .order_by(TimelineClipAsset.asset_role)
        .all()
    )
    assert [link.asset_role for link in links] == ["end_frame", "start_frame"]
    assert {link.clip_id for link in links} == {"video_scene_001_beat_002_001"}


async def _fake_keyframe_generator(**kwargs):
    prompt = kwargs["prompt"]
    if "Opening keyframe" in prompt:
        url = "https://provider.example/start-frame.png"
    elif "Ending keyframe" in prompt:
        url = "https://provider.example/end-frame.png"
    else:
        raise AssertionError(f"unexpected prompt: {prompt}")
    return {
        "urls": [url],
        "provider": "fake",
        "model": "fake-image",
        "image_gen": {"prompt_sha256": "abc123"},
    }


async def _fake_keyframe_persister(**kwargs):
    source_url = kwargs["image_data"]
    filename = source_url.rsplit("/", 1)[-1]
    return {
        "oss_url": f"https://cdn.example/{filename}",
        "local_file_path": f"/tmp/{filename}",
        "relative_path": f"uploads/{filename}",
    }


def _keyframe_payload(timeline, clip_id: str) -> dict:
    return {
        "kind": "timeline_clip_keyframes",
        "timeline_id": timeline.id,
        "timeline_version": timeline.version,
        "expected_version": timeline.version,
        "clip_id": clip_id,
        "model": "fake-image",
        "generation_profile": "clip_keyframes",
        "aspect_ratio": "9:16",
        "reference_images": [],
        "bound_context": {"characters": [], "warnings": []},
        "keyframe_roles": ["start_frame", "end_frame"],
        "frames": [
            {"role": "start_frame", "prompt": "Opening keyframe. Base prompt."},
            {"role": "end_frame", "prompt": "Ending keyframe. Base prompt."},
        ],
    }
