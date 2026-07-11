from __future__ import annotations

from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.production_canvas.stale_runtime import (
    apply_canvas_stale_state,
    canvas_node_input_fingerprint,
    canvas_stale_impact_nodes,
)


def _state() -> ProductionCanvasSavedState:
    return ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "root",
                    "label": "Root",
                    "title": "Root",
                    "status": "ready",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "definition_version": 1,
                    "output_ports": [{"id": "text", "type": "text"}],
                    "outputs": {"text": "v1"},
                },
                {
                    "id": "middle",
                    "label": "Middle",
                    "title": "Middle",
                    "status": "ready",
                    "x": 200,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "input_ports": [{"id": "text", "type": "text", "required": True}],
                    "output_ports": [{"id": "text", "type": "text"}],
                    "outputs": {"text": "middle-v1"},
                },
                {
                    "id": "leaf",
                    "label": "Leaf",
                    "title": "Leaf",
                    "status": "ready",
                    "x": 400,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "input_ports": [{"id": "text", "type": "text", "required": True}],
                },
            ],
            "edges": [
                {
                    "edge_id": "root-middle",
                    "from": "root",
                    "from_port": "text",
                    "to": "middle",
                    "to_port": "text",
                    "binding_type": "value",
                },
                {
                    "edge_id": "middle-leaf",
                    "from": "middle",
                    "from_port": "text",
                    "to": "leaf",
                    "to_port": "text",
                    "binding_type": "value",
                },
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )


def _executed(state: ProductionCanvasSavedState) -> ProductionCanvasSavedState:
    return state.model_copy(
        update={
            "nodes": [
                node.model_copy(
                    update={
                        "execution_input_fingerprint": canvas_node_input_fingerprint(
                            state, node.id
                        )
                    }
                )
                for node in state.nodes
            ]
        }
    )


def test_definition_change_marks_the_node_and_all_descendants_stale():
    previous = _executed(_state())
    incoming = previous.model_copy(
        update={
            "nodes": [
                (
                    node.model_copy(update={"definition_version": 2})
                    if node.id == "root"
                    else node
                )
                for node in previous.nodes
            ]
        }
    )

    unchanged = apply_canvas_stale_state(previous, previous)
    changed = apply_canvas_stale_state(previous, incoming)

    assert {node.status for node in unchanged.nodes} == {"ready"}
    assert {node.id for node in changed.nodes if node.status == "stale"} == {
        "root",
        "middle",
        "leaf",
    }


def test_stale_impact_only_lists_descendants_with_execution_history():
    state = _state()
    state = state.model_copy(
        update={
            "nodes": [
                (
                    node.model_copy(update={"execution_input_fingerprint": "a" * 64})
                    if node.id == "middle"
                    else node
                )
                for node in state.nodes
            ]
        }
    )

    assert [item.model_dump() for item in canvas_stale_impact_nodes(state, "root")] == [
        {"node_id": "middle", "title": "Middle"}
    ]
