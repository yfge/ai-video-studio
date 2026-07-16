from __future__ import annotations

from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.production_canvas.client_state_merge import (
    canvas_client_state_has_stale_runtime,
    merge_canvas_client_state,
)


def _state(nodes: list[dict]) -> ProductionCanvasSavedState:
    return ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": nodes,
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )


def _node(*, status: str, task_status: str, kind: str = "pipeline") -> dict:
    outputs = {
        "task_id": 901,
        "task_status": task_status,
        "story_id": 61,
        "script_id": 301,
        "timeline_id": 502,
    }
    if kind == "note":
        outputs["source_node_id"] = "script"
    return {
        "id": "script-task-901" if kind == "note" else "script",
        "label": "Script",
        "title": "Script",
        "status": status,
        "x": 0,
        "y": 0,
        "width": 220,
        "kind": kind,
        "skill": "script.generate" if kind != "note" else None,
        "definition_version": 2,
        "execution_input_fingerprint": "a" * 64,
        "outputs": outputs,
    }


def test_terminal_task_cannot_regress_with_same_definition_and_fingerprint():
    previous = _state([_node(status="review", task_status="completed")])
    stale = _state([_node(status="running", task_status="processing")])

    assert canvas_client_state_has_stale_runtime(previous, stale)
    merged = merge_canvas_client_state(
        previous,
        stale,
        {
            "story_id": 61,
            "script_id": 301,
            "timeline_id": 502,
        },
    )

    assert merged.nodes[0].status == "review"
    assert merged.nodes[0].outputs["task_status"] == "completed"
    assert merged.nodes[0].outputs["timeline_id"] == 502


def test_terminal_task_evidence_note_participates_in_stale_detection():
    previous = _state([_node(status="review", task_status="completed", kind="note")])
    stale = _state([_node(status="running", task_status="processing", kind="note")])

    assert canvas_client_state_has_stale_runtime(previous, stale)
    merged = merge_canvas_client_state(previous, stale)

    assert merged.nodes[0].status == "review"
    assert merged.nodes[0].outputs["task_status"] == "completed"


def test_deleted_terminal_task_evidence_note_marks_snapshot_stale():
    previous = _state([_node(status="review", task_status="completed", kind="note")])
    stale = _state([])

    assert canvas_client_state_has_stale_runtime(previous, stale)
