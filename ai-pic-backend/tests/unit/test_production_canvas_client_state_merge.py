from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.production_canvas.client_state_merge import (
    canvas_client_state_has_stale_runtime,
    merge_canvas_client_state,
)


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
                "timeline_id": 20,
                "clip_id": "new-clip",
            },
        }
    )
    incoming = _state(
        {
            "definition_version": 1,
            "outputs": {
                "prompt": "保留浏览器中的新参数",
                "script_id": 11,
                "timeline_id": 19,
                "clip_id": "old-clip",
                "approved_image": "stale-browser.png",
            },
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
        "script_id": 10,
        "timeline_id": 20,
        "clip_id": "new-clip",
        "prompt": "保留浏览器中的新参数",
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


def test_stale_client_context_is_applied_to_nodes_added_during_execution():
    server_context = {
        "story_id": 61,
        "episode_id": 175,
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
    }
    previous = _state(
        {
            "execution_input_fingerprint": "b" * 64,
            "outputs": server_context,
        }
    )
    incoming = _state(
        {
            "execution_input_fingerprint": "a" * 64,
            "outputs": {
                "story_id": 60,
                "episode_id": 170,
                "script_id": 140,
                "timeline_id": 501,
                "timeline_version": 7,
                "clip_id": "old-clip",
            },
        }
    )
    added = incoming.nodes[0].model_copy(
        update={
            "id": "new-render",
            "skill": "timeline.render",
            "execution_input_fingerprint": None,
        }
    )
    incoming = incoming.model_copy(update={"nodes": [incoming.nodes[0], added]})

    merged = merge_canvas_client_state(previous, incoming, server_context)

    for node in merged.nodes:
        assert node.outputs["story_id"] == 61
        assert node.outputs["episode_id"] == 175
        assert node.outputs["script_id"] == 301
        assert node.outputs["timeline_id"] == 502
        assert node.outputs["timeline_version"] == 1
        assert "clip_id" not in node.outputs


def test_removing_executed_node_cannot_restore_old_context_from_new_node():
    server_context = {
        "story_id": 61,
        "episode_id": 175,
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
    }
    previous = _state(
        {
            "execution_input_fingerprint": "b" * 64,
            "outputs": server_context,
        }
    )
    incoming = _state(
        {
            "id": "new-render",
            "skill": "timeline.render",
            "outputs": {
                "story_id": 60,
                "episode_id": 170,
                "script_id": 140,
                "timeline_id": 501,
                "timeline_version": 7,
                "clip_id": "old-clip",
            },
        }
    )

    node = merge_canvas_client_state(previous, incoming, server_context).nodes[0]

    assert node.outputs == server_context


def test_older_definition_cannot_undo_timeline_placement_context():
    server_context = {
        "timeline_id": 502,
        "timeline_version": 2,
        "clip_id": "clip-a",
    }
    previous = _state(
        {
            "definition_version": 2,
            "execution_input_fingerprint": "a" * 64,
            "selected_output_id": 42,
            "outputs": server_context,
        }
    )
    incoming = _state(
        {
            "definition_version": 1,
            "execution_input_fingerprint": "a" * 64,
            "selected_output_id": 42,
            "outputs": {
                "timeline_id": 502,
                "timeline_version": 1,
                "clip_id": "clip-old",
            },
        }
    )

    node = merge_canvas_client_state(previous, incoming, server_context).nodes[0]

    assert node.definition_version == 2
    assert node.outputs == server_context


def test_deleting_context_only_node_preserves_authoritative_run_context():
    server_context = {
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 2,
        "clip_id": "clip-a",
    }
    previous = _state({"outputs": server_context})
    incoming = previous.model_copy(update={"nodes": []})

    assert canvas_client_state_has_stale_runtime(previous, incoming)
    merged = merge_canvas_client_state(previous, incoming, server_context)

    assert merged.nodes == []


def test_new_unscoped_node_cannot_override_authoritative_run_context():
    server_context = {
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 2,
        "clip_id": "clip-new",
    }
    previous = _state({"outputs": server_context})
    added = previous.nodes[0].model_copy(
        update={
            "id": "new-render",
            "skill": "timeline.render",
            "outputs": {
                "script_id": 140,
                "timeline_id": 501,
                "timeline_version": 1,
                "clip_id": "clip-old",
            },
        }
    )
    incoming = previous.model_copy(update={"nodes": [previous.nodes[0], added]})

    merged = merge_canvas_client_state(previous, incoming, server_context)

    assert not canvas_client_state_has_stale_runtime(previous, incoming)
    assert merged.nodes[0].outputs == server_context
    assert merged.nodes[1].outputs == server_context


def test_runtime_revision_distinguishes_same_input_reexecution():
    previous = _state(
        {
            "definition_version": 2,
            "execution_input_fingerprint": "a" * 64,
            "outputs": {"timeline_version": 2, "task_id": 200},
        }
    )
    incoming = _state(
        {
            "definition_version": 1,
            "execution_input_fingerprint": "a" * 64,
            "outputs": {"timeline_version": 1, "task_id": 100},
        }
    )

    merged = merge_canvas_client_state(previous, incoming).nodes[0]

    assert merged.definition_version == 2
    assert merged.outputs == {"timeline_version": 2, "task_id": 200}
