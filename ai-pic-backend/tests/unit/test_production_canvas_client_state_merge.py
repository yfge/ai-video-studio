from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.production_canvas.client_state_merge import merge_canvas_client_state


def _state(node: dict) -> ProductionCanvasSavedState:
    return ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "image-review",
                    "label": "Image Candidates",
                    "title": "图片候选",
                    "status": "review",
                    "x": 0,
                    "y": 0,
                    "width": 220,
                    "kind": "pipeline",
                    "skill": "image.candidates",
                    **node,
                }
            ],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )


def test_client_state_cannot_overwrite_server_review_or_runtime_state():
    previous = _state(
        {
            "status": "approved",
            "definition_version": 2,
            "execution_input_fingerprint": "a" * 64,
            "selected_output_id": 42,
            "selected_output_url": "https://example.com/approved.png",
            "selected_output_reviewed_by": 7,
            "selected_output_reviewed_at": "2026-07-11T12:00:00Z",
            "outputs": {
                "approved_image": "https://example.com/approved.png",
                "approved_asset_id": 42,
                "script_id": 10,
            },
        }
    )
    incoming = _state(
        {
            "definition_version": 1,
            "outputs": {"script_id": 11, "approved_image": "stale-browser.png"},
        }
    )

    node = merge_canvas_client_state(previous, incoming).nodes[0]

    assert node.status == "approved"
    assert node.definition_version == 2
    assert node.execution_input_fingerprint == "a" * 64
    assert node.selected_output_id == 42
    assert node.selected_output_reviewed_by == 7
    assert node.outputs == {
        "approved_image": "https://example.com/approved.png",
        "approved_asset_id": 42,
        "script_id": 11,
    }


def test_current_client_runtime_can_update_status_and_outputs():
    previous = _state(
        {
            "status": "ready",
            "execution_input_fingerprint": "a" * 64,
            "outputs": {"production_brief": "old"},
        }
    )
    incoming = _state(
        {
            "status": "failed",
            "execution_input_fingerprint": "a" * 64,
            "outputs": {},
        }
    )

    node = merge_canvas_client_state(previous, incoming).nodes[0]

    assert node.status == "failed"
    assert node.outputs == {}
