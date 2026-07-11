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
        "skill": "brief.compose",
        "definition_version": 1,
        "input_ports": input_ports or [],
        "output_ports": output_ports or [],
    }


def _brief_chain_state(*, block_middle: bool = False) -> dict:
    input_ports = [{"id": "production_brief", "type": "text", "required": True}]
    if block_middle:
        input_ports.append({"id": "episode", "type": "entity_ref", "required": True})
    output_ports = [{"id": "production_brief", "type": "text"}]
    return {
        "graph_version": 2,
        "nodes": [
            _node("root", output_ports=output_ports),
            _node("middle", input_ports=input_ports, output_ports=output_ports),
            _node("leaf", input_ports=input_ports[:1]),
        ],
        "edges": [
            {
                "edge_id": "root-to-middle",
                "from": "root",
                "from_port": "production_brief",
                "to": "middle",
                "to_port": "production_brief",
                "binding_type": "value",
            },
            {
                "edge_id": "middle-to-leaf",
                "from": "middle",
                "from_port": "production_brief",
                "to": "leaf",
                "to_port": "production_brief",
                "binding_type": "value",
            },
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "selected_node_id": "root",
    }


def _create_run(client, state: dict) -> str:
    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "验证下游执行"},
    )
    assert response.status_code == 200
    run_id = response.json()["data"]["run_id"]
    response = client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state)
    assert response.status_code == 200
    return run_id


def _run_downstream(client, run_id: str, prompt: str) -> dict:
    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": prompt,
            "skill": "brief.compose",
            "node_id": "root",
            "run_id": run_id,
            "execution_scope": "downstream",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_run_downstream_executes_in_dependency_order_and_persists_nodes(client):
    run_id = _create_run(client, _brief_chain_state())
    result = _run_downstream(client, run_id, "贯穿三节点的真实输入")

    assert result["execution_order"] == ["root", "middle", "leaf"]
    assert [item["node_id"] for item in result["executions"]] == [
        "root",
        "middle",
        "leaf",
    ]
    for execution in result["executions"][1:]:
        assert execution["resolved_inputs"] == {
            "production_brief": "贯穿三节点的真实输入"
        }

    restored = client.get(f"/api/v1/production-canvas/runs/{run_id}").json()["data"]
    nodes = {node["id"]: node for node in restored["saved_state"]["nodes"]}
    for node_id in ("root", "middle", "leaf"):
        assert nodes[node_id]["outputs"]["prompt"] == "贯穿三节点的真实输入"
        assert len(nodes[node_id]["execution_input_fingerprint"]) == 64


def test_run_downstream_stops_when_an_intermediate_node_is_blocked(client):
    run_id = _create_run(client, _brief_chain_state(block_middle=True))
    result = _run_downstream(client, run_id, "只允许执行到阻塞节点")

    assert result["execution_order"] == ["root", "middle", "leaf"]
    assert [item["node_id"] for item in result["executions"]] == ["root", "middle"]
    blocked = result["executions"][1]["skill_result"]
    assert blocked["status"] == "blocked"
    assert blocked["outputs"]["required_inputs"] == ["episode"]


def test_changed_typed_output_marks_descendants_stale_until_rerun(client):
    run_id = _create_run(client, _brief_chain_state())
    _run_downstream(client, run_id, "第一版生产输入")
    restored = client.get(f"/api/v1/production-canvas/runs/{run_id}").json()["data"]
    state = restored["saved_state"]
    nodes = {node["id"]: node for node in state["nodes"]}
    nodes["root"]["outputs"]["prompt"] = "第二版生产输入"

    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=state,
    )

    assert saved.status_code == 200
    stale_nodes = {
        node["id"]: node for node in saved.json()["data"]["saved_state"]["nodes"]
    }
    assert stale_nodes["root"]["status"] == "ready"
    assert stale_nodes["middle"]["status"] == "stale"
    assert stale_nodes["leaf"]["status"] == "stale"
    evaluation = client.get(f"/api/v1/production-canvas/runs/{run_id}/graph").json()[
        "data"
    ]
    evaluated = {node["node_id"]: node for node in evaluation["node_states"]}
    assert evaluated["middle"]["status"] == "stale"
    assert evaluated["leaf"]["status"] == "stale"
    assert evaluated["leaf"]["missing_inputs"] == ["production_brief"]

    rerun = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "不得覆盖类型化输入",
            "skill": "brief.compose",
            "node_id": "middle",
            "run_id": run_id,
            "execution_scope": "downstream",
        },
    ).json()["data"]

    assert [item["node_id"] for item in rerun["executions"]] == ["middle", "leaf"]
    assert rerun["executions"][0]["resolved_inputs"] == {
        "production_brief": "第二版生产输入"
    }
    refreshed = client.get(f"/api/v1/production-canvas/runs/{run_id}").json()["data"]
    refreshed_nodes = {node["id"]: node for node in refreshed["saved_state"]["nodes"]}
    assert refreshed_nodes["middle"]["status"] == "ready"
    assert refreshed_nodes["leaf"]["status"] == "ready"
