from app.models.user import User
from tests.integration.test_production_canvas_candidate_review_api import (
    _create_script,
    _review_state,
)


def _review_node(payload: dict, node_id: str) -> dict:
    return next(
        item
        for item in payload["data"]["saved_state"]["nodes"]
        if item["id"] == node_id
    )


def test_candidate_rejection_persists_reason_and_clears_selected_output(
    client, db_session
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "拒绝不合格候选", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_review_state(script.id),
    )
    assert saved.status_code == 200
    path = f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review"
    candidates = client.get(f"{path}/candidates").json()["data"]["candidates"]

    approved = client.post(
        f"{path}/approval", json={"candidate_id": candidates[1]["asset_id"]}
    )
    assert approved.status_code == 200
    rejected_unselected = client.post(
        f"{path}/rejection",
        json={"candidate_id": candidates[0]["asset_id"], "reason": "构图偏离镜头"},
    )
    assert rejected_unselected.status_code == 200
    image = _review_node(rejected_unselected.json(), "image-review")
    assert image["status"] == "approved"
    assert image["selected_output_id"] == candidates[1]["asset_id"]
    listed = client.get(f"{path}/candidates").json()["data"]["candidates"]
    assert listed[0]["review_state"] == "rejected"
    assert listed[0]["rejection_reason"] == "构图偏离镜头"
    assert listed[0]["reviewed_by"] == user.id
    assert listed[0]["reviewed_at"]

    reconsidered = client.post(
        f"{path}/approval", json={"candidate_id": candidates[0]["asset_id"]}
    )
    assert reconsidered.status_code == 200
    relisted = client.get(f"{path}/candidates").json()["data"]["candidates"]
    assert relisted[0]["review_state"] == "approved"
    assert relisted[0]["rejection_reason"] is None

    rejected_selected = client.post(
        f"{path}/rejection",
        json={"candidate_id": candidates[0]["asset_id"], "reason": "角色不一致"},
    )
    assert rejected_selected.status_code == 200
    payload = rejected_selected.json()
    image = _review_node(payload, "image-review")
    video = _review_node(payload, "video-review")
    assert image["status"] == "review"
    assert image["selected_output_id"] is None
    assert image["selected_output_url"] is None
    assert "approved_image" not in image["outputs"]
    assert video["status"] == "stale"
    restored = client.get(f"{path}/candidates").json()["data"]
    assert restored["selected_output_id"] is None
    assert restored["candidates"][0]["review_state"] == "rejected"
    assert restored["candidates"][0]["rejection_reason"] == "角色不一致"
