import json

from app.models.task import Task, TaskType
from app.models.timeline import MediaAsset
from app.repositories.timeline_repository import TimelineClipAssetRepository
from tests.test_timeline_clip_video_grid_rework_api import (
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec_with_clip_storyboard,
)
from tests.test_timeline_storyboard_grid_api import _append_video_clips, _timeline_spec


def test_canvas_storyboard_candidates_queue_clip_sheet(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}
    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        lambda task, payload, current_user: dispatched.update(
            task_id=task.id,
            payload=payload,
            user_id=current_user.id,
        ),
    )
    user, episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )
    run_id = "storyboardcapability000000000001"

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "为当前镜头生成故事板",
            "skill": "storyboard.candidates",
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": clip_id,
            "run_id": run_id,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    task = db_session.get(Task, payload["task_id"])
    params = json.loads(task.parameters)
    assert task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
    assert task.target_business_id == run_id
    assert params["kind"] == "timeline_clip_storyboard"
    assert params["clip_id"] == clip_id
    assert params["panel_count"] in {2, 4, 6, 9}
    assert params["model"] == "codex:gpt-image-2"
    assert payload["skill_result"]["outputs"]["panel_count_options"] == [2, 4, 6, 9]
    assert dispatched["task_id"] == task.id
    assert dispatched["user_id"] == user.id


def _storyboard_timeline(client, db_session):
    user, episode, script = _bootstrap_episode(db_session)
    sheet = MediaAsset(
        asset_type="image",
        origin="generated",
        file_url="https://example.com/canvas-clip-storyboard.png",
        mime_type="image/png",
        extra_metadata={"model": "codex:gpt-image-2"},
        created_by=user.id,
    )
    db_session.add(sheet)
    db_session.commit()
    db_session.refresh(sheet)
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _timeline_spec_with_clip_storyboard(episode, script, clip_id, sheet),
    )
    if not TimelineClipAssetRepository(db_session).get_latest_for_clip_role_any_version(
        timeline_id=timeline["id"],
        clip_id=clip_id,
        asset_role="clip_storyboard_sheet",
    ):
        TimelineClipAssetRepository(db_session).create(
            timeline_id=timeline["id"],
            timeline_version=timeline["version"],
            clip_id=clip_id,
            track_type="video",
            asset_role="clip_storyboard_sheet",
            media_asset_id=sheet.id,
            source="timeline_spec",
            created_by=user.id,
        )
        db_session.commit()
    return user, script, timeline, clip_id, sheet


def test_canvas_video_candidates_use_storyboard_without_keyframes_or_auto_render(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}
    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        lambda task, payload, current_user: dispatched.update(payload=payload),
    )
    _, _, timeline, clip_id, sheet = _storyboard_timeline(client, db_session)
    run_id = "storyboardvideo0000000000000001"

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "基于故事板生成视频候选",
            "skill": "video.candidates",
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": clip_id,
            "reference_artifacts": [sheet.file_url],
            "run_id": run_id,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    task = db_session.get(Task, payload["task_id"])
    params = json.loads(task.parameters)
    assert task.task_type == TaskType.VIDEO_GENERATION
    assert task.target_business_id == run_id
    assert params["reference_mode"] == "clip_storyboard_sheet"
    assert params["reference_images"] == [sheet.file_url]
    assert params["image_url"] is None
    assert params["end_image_url"] is None
    assert params["return_last_frame"] is False
    assert params["auto_render"] is False
    assert payload["skill_result"]["outputs"]["uses_start_frame"] is False
    assert payload["skill_result"]["outputs"]["uses_end_frame"] is False
    assert payload["skill_result"]["outputs"]["placement_mode"] == "explicit_node"
    assert dispatched["payload"]["auto_render"] is False


def test_canvas_storyboard_candidate_can_be_approved_for_video_input(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.production_canvas.autonomous_planner.ai_service.ai_manager",
        None,
    )
    _, script, timeline, clip_id, sheet = _storyboard_timeline(client, db_session)
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "评审 clip 故事板", "script_id": script.id},
    ).json()["data"]
    run_id = plan["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json={
            "graph_version": 2,
            "nodes": [
                {
                    "id": "storyboard-review",
                    "label": "Clip Storyboard",
                    "title": "故事板候选",
                    "status": "review",
                    "x": 0,
                    "y": 0,
                    "width": 220,
                    "skill": "storyboard.candidates",
                    "outputs": {
                        "script_id": script.id,
                        "timeline_id": timeline["id"],
                        "timeline_version": timeline["version"],
                        "clip_id": clip_id,
                    },
                    "output_ports": [{"id": "approved_storyboard", "type": "image"}],
                },
                {
                    "id": "video-review",
                    "label": "Video",
                    "title": "视频候选",
                    "status": "ready",
                    "x": 280,
                    "y": 0,
                    "width": 220,
                    "skill": "video.candidates",
                    "execution_input_fingerprint": "a" * 64,
                    "input_ports": [
                        {
                            "id": "approved_storyboard",
                            "type": "image",
                            "required": True,
                        }
                    ],
                },
            ],
            "edges": [
                {
                    "edge_id": "storyboard-to-video",
                    "from": "storyboard-review",
                    "from_port": "approved_storyboard",
                    "to": "video-review",
                    "to_port": "approved_storyboard",
                    "binding_type": "selected_output",
                }
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        },
    )
    assert saved.status_code == 200, saved.text

    candidates = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/storyboard-review/candidates"
    ).json()["data"]["candidates"]
    assert [item["url"] for item in candidates] == [sheet.file_url]
    approved = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/storyboard-review/approval",
        json={"candidate_id": candidates[0]["asset_id"]},
    )

    assert approved.status_code == 200, approved.text
    nodes = approved.json()["data"]["saved_state"]["nodes"]
    storyboard = next(item for item in nodes if item["id"] == "storyboard-review")
    video = next(item for item in nodes if item["id"] == "video-review")
    assert storyboard["outputs"]["approved_storyboard"] == sheet.file_url
    assert storyboard["outputs"]["selected_output_clip_id"] == clip_id
    assert video["status"] == "stale"
