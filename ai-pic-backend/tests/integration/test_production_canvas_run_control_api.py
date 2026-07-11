from __future__ import annotations

import json

from app.models.task import Task, TaskStatus, TaskType
from tests.integration.test_production_canvas_downstream_api import (
    _brief_chain_state,
    _create_run,
)


def _action(client, run_id: str, **payload) -> dict:
    response = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/actions",
        json=payload,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_run_ready_executes_the_server_evaluated_graph(client):
    run_id = _create_run(client, _brief_chain_state())

    result = _action(client, run_id, action="run_ready")

    assert result["execution_order"] == ["root", "middle", "leaf"]
    assert [item["node_id"] for item in result["executions"]] == [
        "root",
        "middle",
        "leaf",
    ]
    assert len(result["run"]["execution_attempts"]) == 3
    assert all(
        item["definition_mode"] == "current"
        for item in result["run"]["execution_attempts"]
    )


def test_resume_skips_valid_outputs_and_retries_interrupted_nodes(client):
    run_id = _create_run(client, _brief_chain_state())
    first = _action(client, run_id, action="run_ready")
    state = first["run"]["saved_state"]
    for node in state["nodes"]:
        if node["id"] == "leaf":
            node["status"] = "failed"
    saved = client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state)
    assert saved.status_code == 200, saved.text

    resumed = _action(client, run_id, action="resume")

    assert resumed["execution_order"] == ["leaf"]
    assert {"root", "middle"}.issubset(resumed["skipped_node_ids"])
    assert len(resumed["run"]["execution_attempts"]) == 4


def test_cancel_stops_active_tasks_without_deleting_outputs(client, db_session):
    state = _brief_chain_state()
    run_id = _create_run(client, state)
    owner_id = db_session.query(Task).filter(Task.business_id == run_id).one().user_id
    task = Task(
        title="画布执行任务",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.PROCESSING,
        prompt="继续执行",
        parameters=json.dumps({}),
        target_business_id=run_id,
        user_id=owner_id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    state["nodes"][0].update(
        {
            "status": "running",
            "outputs": {
                "dispatched_task_id": task.id,
                "completed_output": "保留",
            },
        }
    )
    saved = client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state)
    assert saved.status_code == 200, saved.text

    cancelled = _action(client, run_id, action="cancel")

    assert cancelled["cancelled_task_ids"] == [task.id]
    db_session.refresh(task)
    assert task.status == TaskStatus.CANCELLED
    root = next(
        node
        for node in cancelled["run"]["saved_state"]["nodes"]
        if node["id"] == "root"
    )
    assert root["status"] == "cancelled"
    assert root["outputs"]["completed_output"] == "保留"


def test_retry_selects_original_or_current_definition(client):
    state = _brief_chain_state(block_middle=True)
    state["nodes"][0]["outputs"] = {"prompt": "已完成上游"}
    run_id = _create_run(client, state)
    failed = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "首次失败",
            "skill": "brief.compose",
            "node_id": "middle",
            "run_id": run_id,
        },
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["data"]["skill_result"]["status"] == "blocked"
    run = client.get(f"/api/v1/production-canvas/runs/{run_id}").json()["data"]
    assert run["execution_attempts"][0]["definition_version"] == 1
    state = run["saved_state"]
    middle = next(node for node in state["nodes"] if node["id"] == "middle")
    middle["input_ports"] = [
        port for port in middle["input_ports"] if port["id"] != "episode"
    ]
    middle["definition_version"] = 2
    saved = client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state)
    assert saved.status_code == 200, saved.text

    original = _action(
        client,
        run_id,
        action="retry",
        node_id="middle",
        definition_mode="original",
    )
    current = _action(
        client,
        run_id,
        action="retry",
        node_id="middle",
        definition_mode="current",
    )

    assert original["executions"][0]["skill_result"]["status"] == "blocked"
    assert current["executions"][0]["skill_result"]["status"] == "ready"
    attempts = current["run"]["execution_attempts"]
    assert [item["definition_mode"] for item in attempts] == [
        "current",
        "original",
        "current",
    ]
    assert [item["definition_version"] for item in attempts] == [1, 1, 2]
