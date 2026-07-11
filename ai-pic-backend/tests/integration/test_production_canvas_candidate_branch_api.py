from __future__ import annotations

import copy
import json

from app.models.task import Task
from app.models.timeline import MediaAsset, Timeline
from app.models.user import User
from app.services.storyboard.candidate_lineage import record_canvas_candidate_lineage
from tests.integration.test_production_canvas_candidate_review_api import (
    _create_script,
    _review_state,
    _video_review_state,
)
from tests.integration.test_production_canvas_media_api import _create_storyboard_script


def test_candidate_branch_dispatches_generation_and_persists_child_lineage(
    client, db_session, monkeypatch
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    dispatched = {}

    def fake_delay(task_id, payload, user_id):
        dispatched.update(task_id=task_id, payload=payload, user_id=user_id)

    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        fake_delay,
    )
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "从候选创建视觉分支", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    state = _review_state(script.id)
    state["nodes"][0]["input_ports"] = [
        {"id": "shot_context", "type": "text", "required": True}
    ]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=state,
    )
    assert saved.status_code == 200
    path = f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review"
    parent = client.get(f"{path}/candidates").json()["data"]["candidates"][0]
    approved = client.post(
        f"{path}/approval", json={"candidate_id": parent["asset_id"]}
    )
    assert approved.status_code == 200

    branched = client.post(
        f"{path}/branches",
        json={
            "candidate_id": parent["asset_id"],
            "instruction": "保留构图，改成夜景冷色光",
        },
    )
    assert branched.status_code == 200, branched.text
    node = next(
        item
        for item in branched.json()["data"]["saved_state"]["nodes"]
        if item["id"] == "image-review"
    )
    task_id = node["outputs"]["branch_task_id"]
    assert node["status"] == "running"
    assert node["selected_output_id"] == parent["asset_id"]
    assert node["selected_output_url"] == parent["url"]
    assert node["outputs"]["branch_parent_candidate_id"] == parent["asset_id"]
    assert node["outputs"]["branch_frame_index"] == 1
    assert dispatched["task_id"] == task_id
    assert dispatched["user_id"] == user.id

    task = db_session.get(Task, task_id)
    params = json.loads(task.parameters)
    assert params["frame_indexes"] == [1]
    assert params["reference_images"] == [parent["url"]]
    assert "共享办公区里的智能音箱" in params["prompt"]
    assert params["prompt"].endswith(
        "Branch variation instruction: 保留构图，改成夜景冷色光"
    )
    assert params["canvas_branch"] == {
        "run_id": run_id,
        "node_id": "image-review",
        "parent_candidate_id": parent["asset_id"],
        "instruction": "保留构图，改成夜景冷色光",
    }

    child_url = "https://example.com/frame-2-night.png"
    extra = copy.deepcopy(script.extra_metadata)
    frame = extra["storyboard"]["frames"][1]
    frame["start_image_urls"].append(child_url)
    record_canvas_candidate_lineage(
        frame, [child_url], params["canvas_branch"], task_id=task_id
    )
    script.extra_metadata = extra
    db_session.add(script)
    db_session.commit()

    candidates = client.get(f"{path}/candidates").json()["data"]["candidates"]
    child = next(item for item in candidates if item["url"] == child_url)
    assert child["parent_candidate_id"] == parent["asset_id"]
    assert child["branch_task_id"] == task_id
    assert child["branch_instruction"] == "保留构图，改成夜景冷色光"
    asset = db_session.get(MediaAsset, child["asset_id"])
    reference = next(
        item
        for item in asset.extra_metadata["canvas_candidate_refs"]
        if item["run_id"] == run_id and item["node_id"] == "image-review"
    )
    assert reference["parent_candidate_id"] == parent["asset_id"]
    assert reference["branch_task_id"] == task_id


def test_candidate_branch_rejects_assets_outside_the_review_node(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "拒绝未知父候选", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_review_state(script.id),
    )
    response = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/branches",
        json={"candidate_id": 999999},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "canvas_candidate_not_found"


def test_video_candidate_branch_reuses_its_frame_and_records_task_context(
    client, db_session, monkeypatch
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_storyboard_script(db_session, user)
    timeline = (
        db_session.query(Timeline)
        .filter(Timeline.script_id == script.id)
        .order_by(Timeline.id.desc())
        .first()
    )
    extra = copy.deepcopy(script.extra_metadata)
    extra["storyboard"]["frames"][1]["video_urls"] = [
        "https://example.com/parent-video.mp4"
    ]
    script.extra_metadata = extra
    db_session.add(script)
    db_session.commit()
    dispatched = {}

    def fake_delay(task_id, payload, user_id):
        dispatched.update(task_id=task_id, payload=payload, user_id=user_id)

    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        fake_delay,
    )
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "从视频候选创建分支", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    state = _video_review_state(script.id, timeline.id, timeline.version)
    state["nodes"][0]["input_ports"] = [
        {"id": "start_frame", "type": "image", "required": True}
    ]
    client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=state,
    )
    path = f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review"
    parent = client.get(f"{path}/candidates").json()["data"]["candidates"][0]

    response = client.post(
        f"{path}/branches",
        json={"candidate_id": parent["asset_id"], "instruction": "运动节奏更慢"},
    )
    assert response.status_code == 200, response.text
    node = response.json()["data"]["saved_state"]["nodes"][0]
    task_id = node["outputs"]["branch_task_id"]
    task = db_session.get(Task, task_id)
    params = json.loads(task.parameters)
    assert params["frame_indexes"] == [1]
    assert params["selections"] == [
        {
            "frame_index": 1,
            "start_image_url": "https://example.com/start-frame-2-latest.png",
        }
    ]
    assert params["canvas_branch"]["parent_candidate_id"] == parent["asset_id"]
    assert params["canvas_branch"]["instruction"] == "运动节奏更慢"
    assert params["prompt"].endswith("Branch variation instruction: 运动节奏更慢")
    assert dispatched["task_id"] == task_id
