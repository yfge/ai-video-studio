from __future__ import annotations


def _node(
    node_id: str,
    *,
    input_ports: list[dict] | None = None,
    output_ports: list[dict] | None = None,
) -> dict:
    return {
        "id": node_id,
        "label": node_id.title(),
        "title": f"{node_id} node",
        "status": "ready",
        "x": 0,
        "y": 0,
        "width": 200,
        "kind": "pipeline",
        "definition_version": 1,
        "input_ports": input_ports or [],
        "output_ports": output_ports or [],
    }


def _typed_state() -> dict:
    return {
        "graph_version": 2,
        "nodes": [
            _node(
                "image",
                output_ports=[{"id": "approved_image", "type": "image"}],
            ),
            _node(
                "video",
                input_ports=[{"id": "start_frame", "type": "image", "required": True}],
            ),
        ],
        "edges": [
            {
                "edge_id": "image-approved-to-video-start",
                "from": "image",
                "from_port": "approved_image",
                "to": "video",
                "to_port": "start_frame",
                "binding_type": "selected_output",
                "required": True,
            }
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "selected_node_id": "video",
    }


def _create_run(client) -> str:
    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "验证类型化画布图"},
    )
    assert response.status_code == 200
    return response.json()["data"]["run_id"]


def test_typed_canvas_graph_api_saves_and_restores_bindings(client):
    run_id = _create_run(client)
    state = _typed_state()

    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=state,
    )

    assert saved.status_code == 200
    saved_state = saved.json()["data"]["saved_state"]
    assert saved_state["graph_version"] == 2
    assert saved_state["edges"][0]["from_port"] == "approved_image"
    assert saved_state["edges"][0]["to_port"] == "start_frame"

    restored = client.get(f"/api/v1/production-canvas/runs/{run_id}")
    assert restored.status_code == 200
    restored_state = restored.json()["data"]["saved_state"]
    assert restored_state == saved_state


def test_typed_canvas_graph_api_rejects_incompatible_binding(client):
    run_id = _create_run(client)
    state = _typed_state()
    state["nodes"][1]["input_ports"][0]["type"] = "video"

    response = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=state,
    )

    assert response.status_code == 422
    assert "Incompatible canvas port types" in response.text
