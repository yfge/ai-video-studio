from app.models.script import Episode
from app.models.timeline import MediaAsset, TimelineClipAsset
from app.models.user import User
from tests.integration.test_production_canvas_timeline_placement_api import (
    CLIP_B,
    _approve_and_place,
    _create_script,
    _create_timeline,
    _node,
    _prepare_run,
)


def test_approved_video_is_explicitly_placed_in_versioned_timeline(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user, (CLIP_B,))
    timeline = _create_timeline(client, script, (CLIP_B,))
    plan, (node_id,) = _prepare_run(client, script, timeline, (CLIP_B,))

    candidate, placed = _approve_and_place(client, plan["run_id"], node_id, 1)
    video = _node(placed, node_id)
    render = _node(placed, "timeline-render")
    assert video["outputs"]["timeline_version"] == 2
    assert video["outputs"]["placed_timeline_clip_id"] == CLIP_B
    assert render["outputs"]["timeline_version"] == 2
    assert render["outputs"]["clip_id"] == CLIP_B
    assert placed["resolved_context"]["timeline_version"] == 2
    assert placed["resolved_context"]["clip_id"] == CLIP_B
    assert (
        placed["resolved_context"]["story_id"]
        == db_session.get(Episode, script.episode_id).story_id
    )
    task = client.get(f"/api/v1/tasks/{plan['task_id']}")
    assert task.json()["result_context"]["timeline_version"] == 2
    assert task.json()["result_context"]["clip_id"] == CLIP_B
    current = client.get(f"/api/v1/timelines/{timeline['id']}").json()
    clip = current["spec"]["tracks"][0]["clips"][0]
    assert current["version"] == 2
    assert clip["asset_ref"]["media_asset_id"] == candidate["asset_id"]
    assert clip["asset_ref"]["url"] == candidate["url"]
    lineage = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"timeline_version": 2, "clip_id": CLIP_B},
    ).json()["items"]
    assert lineage[0]["media_asset_id"] == candidate["asset_id"]
    assert lineage[0]["asset_role"] == "generated_video"

    generated = MediaAsset(
        asset_type="video",
        origin="provider_rework",
        file_url="https://example.com/generated-v2.mp4",
        created_by=user.id,
    )
    db_session.add(generated)
    db_session.flush()
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline["id"],
            timeline_version=2,
            clip_id=CLIP_B,
            track_type="video",
            asset_role="generated_video",
            media_asset_id=generated.id,
            source="provider_rework",
            created_by=user.id,
        )
    )
    db_session.commit()
    base = f"/api/v1/production-canvas/runs/{plan['run_id']}/nodes/{node_id}"
    relisted = client.get(f"{base}/candidates").json()["data"]["candidates"]
    assert relisted[-1]["url"] == "https://example.com/generated-v2.mp4"
    assert (
        client.post(
            f"{base}/timeline-placement", json={"expected_version": 1}
        ).status_code
        == 409
    )
