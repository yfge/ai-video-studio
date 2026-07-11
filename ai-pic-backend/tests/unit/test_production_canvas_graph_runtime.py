from __future__ import annotations

from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.production_canvas.graph_runtime import evaluate_canvas_graph


def test_graph_evaluation_orders_disconnected_dag_and_preserves_review_state():
    state = ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "source",
                    "label": "Source",
                    "title": "Source",
                    "status": "approved",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "output_ports": [{"id": "text", "type": "text"}],
                    "outputs": {"text": "ready"},
                },
                {
                    "id": "target",
                    "label": "Target",
                    "title": "Target",
                    "status": "blocked",
                    "x": 200,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "input_ports": [{"id": "text", "type": "text", "required": True}],
                },
                {
                    "id": "independent",
                    "label": "Independent",
                    "title": "Independent",
                    "status": "review",
                    "x": 0,
                    "y": 200,
                    "width": 200,
                    "kind": "pipeline",
                },
            ],
            "edges": [
                {
                    "edge_id": "source-to-target",
                    "from": "source",
                    "from_port": "text",
                    "to": "target",
                    "to_port": "text",
                    "binding_type": "value",
                }
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )

    evaluation = evaluate_canvas_graph(state)
    states = {item.node_id: item for item in evaluation.node_states}

    assert evaluation.execution_order.index(
        "source"
    ) < evaluation.execution_order.index("target")
    assert set(evaluation.execution_order) == {"source", "target", "independent"}
    assert states["source"].status == "approved"
    assert states["target"].status == "ready"
    assert states["target"].missing_inputs == []
    assert states["independent"].status == "review"
