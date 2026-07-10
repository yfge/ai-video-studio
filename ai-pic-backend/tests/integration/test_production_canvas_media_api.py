from __future__ import annotations

import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User


def _storyboard_frames() -> list[dict]:
    return [
        {
            "scene_number": 1,
            "description": "林妹妹在共享办公区调试智能音箱",
            "ai_prompt": "共享办公区里，年轻程序员正在调试智能音箱",
            "duration_seconds": 3.2,
            "reference_images": ["https://example.com/office-ref.png"],
            "image_url": "https://example.com/start-frame.png",
            "end_image_url": "https://example.com/end-frame.png",
        },
        {
            "scene_number": 1,
            "description": "程序员发现音箱开始吐槽代码",
            "ai_prompt": "程序员错愕地看向会说话的智能音箱",
            "duration_seconds": 2.8,
            "reference_images": ["https://example.com/device-ref.png"],
            "image_url": "https://example.com/start-frame-2.png",
            "start_image_urls": [
                "https://example.com/start-frame-2.png",
                "https://example.com/start-frame-2-latest.png",
            ],
        },
    ]


def _create_storyboard_script(db_session, user: User) -> Script:
    story = Story(user_id=user.id, title="程序员轻喜剧", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=4, title="智能生活入门")
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="第 4 集剧本",
        content="办公室轻喜剧",
        extra_metadata={"storyboard": {"frames": _storyboard_frames()}},
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def test_production_canvas_execute_image_skill_dispatches_existing_task(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_storyboard_script(db_session, user)
    dispatched = {}

    def fake_delay(task_id, params, user_id):
        dispatched["task_id"] = task_id
        dispatched["params"] = params
        dispatched["user_id"] = user_id

    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "生成现有分镜的图片候选",
            "skill": "image.candidates",
            "script_id": script.id,
            "frame_indexes": [1],
            "model": "codex:gpt-image-2",
            "aspect_ratio": "16:9",
            "require_reference_images": False,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_status"] == "pending"
    assert payload["skill_result"]["skill"] == "image.candidates"
    assert payload["skill_result"]["outputs"]["queued_frame_count"] == 1
    assert (
        payload["skill_result"]["outputs"]["dispatched_task_id"] == payload["task_id"]
    )

    task = db_session.get(Task, payload["task_id"])
    params = json.loads(task.parameters)
    assert task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
    assert task.target_business_id == "abcdabcdabcdabcdabcdabcdabcdabcd"
    assert params["script_id"] == script.id
    assert params["frame_indexes"] == [1]
    assert params["model"] == "codex:gpt-image-2"
    assert params["aspect_ratio"] == "16:9"
    assert params["require_reference_images"] is False
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["script_id"] == script.id


def test_production_canvas_execute_video_skill_dispatches_existing_task(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_storyboard_script(db_session, user)
    dispatched = {}

    def fake_delay(task_id, params, user_id):
        dispatched["task_id"] = task_id
        dispatched["params"] = params
        dispatched["user_id"] = user_id

    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "生成现有分镜的视频候选",
            "skill": "video.candidates",
            "script_id": script.id,
            "frame_indexes": [1],
            "model": "minimax:video-01",
            "duration": 6,
            "fps": 30,
            "resolution": "1080p",
            "ratio": "16:9",
            "camera_fixed": True,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_status"] == "pending"
    assert payload["skill_result"]["skill"] == "video.candidates"
    assert payload["skill_result"]["outputs"]["frame_count"] == 2
    assert payload["skill_result"]["outputs"]["selected_candidate_count"] == 1
    assert (
        payload["skill_result"]["outputs"]["dispatched_task_id"] == payload["task_id"]
    )

    task = db_session.get(Task, payload["task_id"])
    params = json.loads(task.parameters)
    assert task.task_type == TaskType.VIDEO_GENERATION
    assert task.target_business_id == "abcdabcdabcdabcdabcdabcdabcdabcd"
    assert params["script_id"] == script.id
    assert params["frame_indexes"] == [1]
    assert params["model"] == "minimax:video-01"
    assert params["duration"] == 6
    assert params["fps"] == 30
    assert params["resolution"] == "1080p"
    assert params["ratio"] == "16:9"
    assert params["camera_fixed"] is True
    assert params["return_last_frame"] is True
    assert params["selections"] == [
        {
            "frame_index": 1,
            "start_image_url": "https://example.com/start-frame-2-latest.png",
        }
    ]
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["script_id"] == script.id


def test_production_canvas_execute_report_skill_summarizes_existing_task(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    task = Task(
        title="生产画布整体创建",
        description="Production canvas skill run",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.COMPLETED,
        prompt="基于林妹妹做第 4 集",
        parameters=json.dumps(
            {
                "kind": "production_canvas_run",
                "prompt": "基于林妹妹做第 4 集",
                "selected_assets": {"virtual_ips": [{"name": "林妹妹"}]},
            },
            ensure_ascii=False,
        ),
        result_file_path="production_canvas:abcdabcdabcdabcdabcdabcdabcdabcd",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "汇总这次画布执行证据",
            "skill": "report.summarize",
            "task_id": task.id,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"] == task.id
    assert payload["task_status"] == "completed"
    assert payload["skill_result"]["skill"] == "report.summarize"
    assert payload["skill_result"]["status"] == "review"
    assert payload["skill_result"]["outputs"]["task_type"] == "text_generation"
    assert payload["skill_result"]["outputs"]["source_kind"] == (
        "production_canvas_run"
    )
    assert "生产画布整体创建" in payload["skill_result"]["detail"]
