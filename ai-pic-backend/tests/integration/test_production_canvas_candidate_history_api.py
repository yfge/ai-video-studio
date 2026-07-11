from copy import deepcopy

from app.models.timeline import MediaAsset
from app.models.user import User
from tests.integration.test_production_canvas_candidate_review_api import (
    _create_script,
    _review_state,
)


def test_candidate_history_survives_storyboard_replacement(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "保留历史候选", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_review_state(script.id),
    )
    assert saved.status_code == 200

    path = f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review"
    listed = client.get(f"{path}/candidates").json()["data"]["candidates"]
    approved = client.post(
        f"{path}/approval", json={"candidate_id": listed[1]["asset_id"]}
    )
    assert approved.status_code == 200

    metadata = deepcopy(script.extra_metadata)
    for frame in metadata["storyboard"]["frames"]:
        frame.pop("image_url", None)
        frame.pop("start_image_url", None)
        frame.pop("start_image_urls", None)
    script.extra_metadata = metadata
    db_session.commit()

    restored = client.get(f"{path}/candidates").json()["data"]

    assert [item["url"] for item in restored["candidates"]] == [
        "https://example.com/frame-2.png",
        "https://example.com/frame-2-latest.png",
    ]
    assert [item["selected"] for item in restored["candidates"]] == [False, True]
    assets = db_session.query(MediaAsset).filter(MediaAsset.asset_type == "image").all()
    references = [
        reference
        for asset in assets
        for reference in (asset.extra_metadata or {}).get("canvas_candidate_refs", [])
    ]
    assert {(item["run_id"], item["node_id"]) for item in references} == {
        (run_id, "image-review")
    }
