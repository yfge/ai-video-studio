from __future__ import annotations

from copy import deepcopy

import pytest
from app.schemas.production_canvas import ProductionCanvasSavedState
from pydantic import ValidationError


def _node(
    node_id: str,
    *,
    input_ports: list[dict] | None = None,
    output_ports: list[dict] | None = None,
    kind: str = "pipeline",
) -> dict:
    return {
        "id": node_id,
        "label": node_id.title(),
        "title": f"{node_id} node",
        "status": "ready",
        "x": 0,
        "y": 0,
        "width": 200,
        "kind": kind,
        "definition_version": 1,
        "input_ports": input_ports or [],
        "output_ports": output_ports or [],
    }


def _port(port_id: str, port_type: str, *, multiple: bool = False) -> dict:
    return {"id": port_id, "type": port_type, "multiple": multiple}


def _typed_state() -> dict:
    return {
        "graph_version": 2,
        "nodes": [
            _node("image", output_ports=[_port("approved_image", "image")]),
            _node("video", input_ports=[_port("start_frame", "image")]),
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
    }


def test_typed_canvas_graph_accepts_compatible_port_binding():
    state = ProductionCanvasSavedState.model_validate(_typed_state())

    assert state.graph_version == 2
    assert state.edges[0].from_port == "approved_image"
    assert state.edges[0].to_port == "start_frame"
    assert state.edges[0].binding_type == "selected_output"


def test_legacy_canvas_graph_remains_compatible_without_ports():
    state = ProductionCanvasSavedState.model_validate(
        {
            "nodes": [_node("image"), _node("video")],
            "edges": [{"from": "image", "to": "video"}],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )

    assert state.graph_version == 1
    assert state.edges[0].edge_id is None


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda data: data["edges"][0].update({"to": "missing"}), "unknown node"),
        (
            lambda data: data["edges"][0].update({"from_port": "missing"}),
            "unknown port",
        ),
        (
            lambda data: data["nodes"][1]["input_ports"][0].update({"type": "video"}),
            "Incompatible canvas port types",
        ),
        (
            lambda data: data["edges"].append(deepcopy(data["edges"][0])),
            "Duplicate canvas edge id",
        ),
        (
            lambda data: data["edges"][0].update(
                {"to": "image", "to_port": "approved_image"}
            ),
            "self-referential",
        ),
    ],
)
def test_typed_canvas_graph_rejects_invalid_bindings(mutation, message):
    payload = _typed_state()
    mutation(payload)

    with pytest.raises(ValidationError, match=message):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_rejects_cycles():
    payload = _typed_state()
    payload["nodes"][0]["input_ports"] = [_port("image_input", "image")]
    payload["nodes"][1]["output_ports"] = [_port("video_frame", "image")]
    payload["edges"].append(
        {
            "edge_id": "video-frame-to-image-input",
            "from": "video",
            "from_port": "video_frame",
            "to": "image",
            "to_port": "image_input",
            "binding_type": "value",
        }
    )

    with pytest.raises(ValidationError, match="cannot contain cycles"):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_rejects_duplicate_binding_with_distinct_edge_id():
    payload = _typed_state()
    duplicate = deepcopy(payload["edges"][0])
    duplicate["edge_id"] = "second-edge-id"
    payload["edges"].append(duplicate)

    with pytest.raises(ValidationError, match="Duplicate canvas edge binding"):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_rejects_note_as_executable_target():
    payload = _typed_state()
    payload["nodes"][1]["kind"] = "note"

    with pytest.raises(ValidationError, match="cannot be executable edge targets"):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_rejects_duplicate_port_ids():
    payload = _typed_state()
    payload["nodes"][0]["output_ports"].append(_port("approved_image", "image"))

    with pytest.raises(ValidationError, match="output port ids must be unique"):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_rejects_multiple_bindings_to_single_input():
    payload = _typed_state()
    payload["nodes"].insert(
        1,
        _node("storyboard", output_ports=[_port("approved_image", "image")]),
    )
    payload["edges"].append(
        {
            "edge_id": "storyboard-approved-to-video-start",
            "from": "storyboard",
            "from_port": "approved_image",
            "to": "video",
            "to_port": "start_frame",
            "binding_type": "selected_output",
        }
    )

    with pytest.raises(ValidationError, match="accepts only one binding"):
        ProductionCanvasSavedState.model_validate(payload)


def test_typed_canvas_graph_requires_stable_order_for_multiple_bindings():
    payload = _typed_state()
    payload["nodes"][1]["input_ports"][0]["multiple"] = True

    with pytest.raises(ValidationError, match="require binding_order"):
        ProductionCanvasSavedState.model_validate(payload)

    payload["edges"][0]["binding_order"] = 0
    state = ProductionCanvasSavedState.model_validate(payload)
    assert state.edges[0].binding_order == 0
