import json

from app.models.task import Task, TaskType
from tests.test_timeline_storyboard_grid_api import (
    _append_video_clips,
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec,
)


def test_timeline_clip_keyframes_creates_generation_task_for_selected_clip(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["task_id"] = task.id
        dispatched["payload"] = payload
        dispatched["user_id"] = current_user.id

    monkeypatch.setattr(
        "app.services.timeline_clip_keyframe_service."
        "dispatch_timeline_clip_keyframe_task",
        fake_dispatch,
    )
    _, episode, script = _bootstrap_episode(db_session)
    spec = _append_video_clips(_timeline_spec(episode, script))
    video_clip = spec["tracks"][1]["clips"][1]
    video_clip["source_refs"] = {
        "timeline_shot_plan": {
            "visual_prompt": "陈哲坐在雨夜车内，手机屏幕冷光照亮侧脸",
            "video_prompt": "镜头缓慢推近，雨水沿车窗滑落",
            "camera_movement": "slow push-in",
            "motion_timeline": [
                {"at_ms": 0, "action": "他低头盯着手机屏幕"},
                {"at_ms": 1200, "action": "他抬眼看向雨中的车窗"},
            ],
            "emotional_landing": "克制的怀疑落点",
        }
    }
    timeline = _create_timeline(client, episode, script, spec)

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_002_001/keyframes/generate",
        json={
            "expected_version": timeline["version"],
            "prompt": "雨夜车内对峙",
            "model": "openai:gpt-image-2",
            "generation_profile": "clip_keyframes",
            "aspect_ratio": "9:16",
            "reference_images": ["https://cdn.example/manual-ref.png"],
            "character_virtual_ip_ids": [32],
            "character_reference_images": ["https://cdn.example/courier.png"],
            "environment_reference_images": ["https://cdn.example/interior.png"],
        },
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]
    task = db_session.get(Task, task_id)
    assert task is not None
    assert task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
    params = json.loads(task.parameters)
    assert params["kind"] == "timeline_clip_keyframes"
    assert params["timeline_id"] == timeline["id"]
    assert params["timeline_version"] == timeline["version"]
    assert params["clip_id"] == "video_scene_001_beat_002_001"
    assert params["generation_profile"] == "clip_keyframes"
    assert params["keyframe_roles"] == ["start_frame", "end_frame"]
    assert params["character_virtual_ip_ids"] == [32]
    assert params["character_reference_images"] == ["https://cdn.example/courier.png"]
    assert params["environment_reference_images"] == [
        "https://cdn.example/interior.png"
    ]
    assert "https://cdn.example/courier.png" in params["reference_images"]
    assert "https://cdn.example/interior.png" in params["reference_images"]
    assert "https://cdn.example/manual-ref.png" in params["reference_images"]
    assert [frame["role"] for frame in params["frames"]] == [
        "start_frame",
        "end_frame",
    ]
    assert params["prompt_contract_version"] == "timeline_clip_visual_prompt_v1"
    assert params["visual_prompt_source"] == "timeline_shot_plan.visual_prompt"
    assert params["motion_prompt_source"] == "operator_override"
    assert "他低头盯着手机屏幕" in params["frames"][0]["prompt"]
    assert "他抬眼看向雨中的车窗" in params["frames"][1]["prompt"]
    assert params["frames"][0]["prompt"] != params["frames"][1]["prompt"]
    assert "Opening keyframe" in params["frames"][0]["prompt"]
    assert "Ending keyframe" in params["frames"][1]["prompt"]
    assert dispatched["task_id"] == task_id
    assert dispatched["payload"]["clip_id"] == "video_scene_001_beat_002_001"


def test_timeline_clip_keyframes_rejects_non_video_clip(client, db_session):
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client, episode, script, _timeline_spec(episode, script)
    )

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/dialogue_scene_001_beat_001_001/keyframes/generate",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "clip keyframes require a video clip"
