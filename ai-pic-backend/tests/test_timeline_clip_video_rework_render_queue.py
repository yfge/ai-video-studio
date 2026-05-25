import json

from app.models.timeline import RenderJob
from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.timeline_render_hash import render_preset_hash
from app.services.video.video_task_timeline_rework_updater import (
    apply_timeline_rework_result,
)
from tests.test_timeline_clip_video_rework_api import (
    _append_video_clip,
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec,
)


def test_video_task_success_queues_rework_render_job(client, db_session, monkeypatch):
    dispatched = {}

    def fake_dispatch(job, *, user_id):
        dispatched["render_job_id"] = job.id
        dispatched["user_id"] = user_id

    monkeypatch.setattr(
        "app.services.video.video_task_timeline_rework_updater."
        "dispatch_provider_rework_render_job",
        fake_dispatch,
    )
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    original_video = _media_asset(
        db_session,
        asset_type="video",
        origin="upload",
        file_url="https://example.com/generated-v1.mp4",
        mime_type="video/mp4",
    )
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clip(
            _timeline_spec(episode, script),
            clip_id=clip_id,
            video_asset=original_video,
        ),
    )
    base_preset = {"fps": 24, "resolution": "1080x1920"}
    existing_render = RenderJob(
        timeline_id=timeline["id"],
        timeline_version=timeline["version"],
        render_type="final",
        preset_hash=render_preset_hash(base_preset),
        preset=base_preset,
        status="succeeded",
        progress=100,
        created_by=user.id,
    )
    db_session.add(existing_render)
    db_session.commit()
    db_session.refresh(existing_render)

    params = {
        "timeline_rework": {
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": clip_id,
            "action": "re_render",
            "asset_role": "generated_video",
            "auto_render": True,
            "render_type": "final",
            "render_preset": base_preset,
        }
    }
    video_task = VideoGenerationTask(
        task_id=None,
        script_id=None,
        frame_index=None,
        user_id=user.id,
        provider="mock-provider",
        provider_task_id="provider-task-2",
        model="mock-video",
        model_type="image_to_video",
        prompt="Regenerate and render the clip",
        parameters=json.dumps(params),
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(video_task)
    db_session.commit()
    db_session.refresh(video_task)

    apply_timeline_rework_result(
        db_session,
        video_task,
        {"video_url": "https://example.com/generated-v3.mp4", "duration": 1.2},
        params,
    )

    render_jobs = (
        db_session.query(RenderJob)
        .filter(RenderJob.timeline_id == timeline["id"])
        .filter(RenderJob.render_type == "final")
        .order_by(RenderJob.id)
        .all()
    )
    assert len(render_jobs) == 2
    queued_render = render_jobs[-1]
    assert queued_render.id != existing_render.id
    assert queued_render.status == "queued"
    assert queued_render.preset_hash != existing_render.preset_hash
    assert queued_render.preset["rework"]["source"] == "provider_rework"
    assert queued_render.preset["rework"]["clip_id"] == clip_id
    assert queued_render.preset["rework"]["video_generation_task_id"] == video_task.id
    assert queued_render.preset["rework"]["provider_task_id"] == "provider-task-2"
    assert dispatched == {"render_job_id": queued_render.id, "user_id": user.id}
