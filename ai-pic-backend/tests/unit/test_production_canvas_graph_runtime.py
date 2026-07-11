from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
)
from app.services.production_canvas.graph_runtime import (
    evaluate_canvas_graph,
    resolve_canvas_graph_request,
)


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


def test_selected_image_resolves_as_explicit_video_start_frame():
    state = ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "image",
                    "label": "Image",
                    "title": "Image candidates",
                    "status": "approved",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "selected_output_id": 42,
                    "selected_output_url": "https://example.com/approved.png",
                    "output_ports": [{"id": "approved_image", "type": "image"}],
                },
                {
                    "id": "video",
                    "label": "Video",
                    "title": "Video candidates",
                    "status": "ready",
                    "x": 240,
                    "y": 0,
                    "width": 200,
                    "kind": "pipeline",
                    "skill": "video.candidates",
                    "input_ports": [
                        {"id": "start_frame", "type": "image", "required": True}
                    ],
                },
            ],
            "edges": [
                {
                    "edge_id": "approved-image-to-video",
                    "from": "image",
                    "from_port": "approved_image",
                    "to": "video",
                    "to_port": "start_frame",
                    "binding_type": "selected_output",
                }
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )
    request = ProductionCanvasSkillExecuteRequest(
        prompt="生成视频",
        skill="video.candidates",
        node_id="video",
        frame_indexes=[0],
    )

    resolution = resolve_canvas_graph_request(state, request)

    assert resolution is not None
    assert resolution.resolved_inputs == {
        "start_frame": "https://example.com/approved.png"
    }
    assert resolution.request.start_frame_url == "https://example.com/approved.png"
