from app.models.user import User
from tests.integration.test_production_canvas_timeline_placement_api import (
    CLIP_A,
    _create_script,
    _create_timeline,
)


def test_timeline_place_node_places_approved_video_and_returns_new_version(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.production_canvas.autonomous_planner.ai_service.ai_manager",
        None,
    )
    user = db_session.query(User).filter_by(username="test_admin").one()
    script = _create_script(db_session, user, (CLIP_A,))
    timeline = _create_timeline(client, script, (CLIP_A,))
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "选片并回填 Timeline", "script_id": script.id},
    ).json()["data"]
    run_id = plan["run_id"]
    state = {
        "graph_version": 2,
        "nodes": [
            {
                "id": "timeline-source",
                "label": "Timeline",
                "title": "当前 Timeline clip",
                "status": "ready",
                "x": 0,
                "y": 0,
                "width": 220,
                "skill": "timeline.assemble",
                "outputs": {
                    "script_id": script.id,
                    "timeline_id": timeline["id"],
                    "timeline_version": timeline["version"],
                    "clip_id": CLIP_A,
                },
                "output_ports": [{"id": "timeline_clip", "type": "entity_ref"}],
            },
            {
                "id": "video-review",
                "label": "Video",
                "title": "视频候选",
                "status": "review",
                "x": 280,
                "y": 0,
                "width": 220,
                "skill": "video.candidates",
                "outputs": {
                    "script_id": script.id,
                    "timeline_id": timeline["id"],
                    "timeline_version": timeline["version"],
                    "clip_id": CLIP_A,
                    "frame_indexes": [0],
                },
                "output_ports": [{"id": "approved_video", "type": "video"}],
            },
            {
                "id": "timeline-place",
                "label": "Timeline Placement",
                "title": "回填 Timeline",
                "status": "blocked",
                "x": 560,
                "y": 0,
                "width": 220,
                "skill": "timeline.place",
                "input_ports": [
                    {
                        "id": "timeline_clip",
                        "type": "entity_ref",
                        "required": True,
                    },
                    {"id": "approved_video", "type": "video", "required": True},
                ],
                "output_ports": [{"id": "placed_timeline", "type": "entity_ref"}],
            },
        ],
        "edges": [
            {
                "edge_id": "timeline-to-place",
                "from": "timeline-source",
                "from_port": "timeline_clip",
                "to": "timeline-place",
                "to_port": "timeline_clip",
                "binding_type": "value",
            },
            {
                "edge_id": "video-to-place",
                "from": "video-review",
                "from_port": "approved_video",
                "to": "timeline-place",
                "to_port": "approved_video",
                "binding_type": "selected_output",
            },
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }
    assert (
        client.put(
            f"/api/v1/production-canvas/runs/{run_id}/state",
            json=state,
        ).status_code
        == 200
    )
    candidates = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/candidates"
    ).json()["data"]["candidates"]
    approved = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/approval",
        json={"candidate_id": candidates[0]["asset_id"]},
    )
    assert approved.status_code == 200, approved.text

    placed = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "回填选用视频",
            "skill": "timeline.place",
            "run_id": run_id,
            "node_id": "timeline-place",
            "script_id": script.id,
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": CLIP_A,
        },
    )

    assert placed.status_code == 200, placed.text
    payload = placed.json()["data"]
    assert payload["skill_result"]["skill"] == "timeline.place"
    assert payload["resolved_context"]["timeline_version"] == 2
    restored = client.get(f"/api/v1/production-canvas/runs/{run_id}").json()["data"]
    placement = next(
        item
        for item in restored["saved_state"]["nodes"]
        if item["id"] == "timeline-place"
    )
    assert placement["outputs"]["placed_timeline"] == timeline["id"]
    assert placement["outputs"]["timeline_version"] == 2
    assert placement["outputs"]["clip_id"] == CLIP_A
