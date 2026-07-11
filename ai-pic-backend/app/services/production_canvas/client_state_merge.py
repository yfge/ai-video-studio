from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
)

_CONFIG_OUTPUT_KEYS = {
    "aspect_ratio",
    "camera_fixed",
    "duration",
    "environment_id",
    "episode_id",
    "fps",
    "frame_indexes",
    "media_model",
    "model",
    "prompt",
    "ratio",
    "require_reference_images",
    "resolution",
    "script_id",
    "video_aspect_ratio",
    "video_duration",
    "video_fps",
    "video_resolution",
    "virtual_ip_id",
}


def _merge_client_node(
    previous: ProductionCanvasSavedNode, incoming: ProductionCanvasSavedNode
) -> ProductionCanvasSavedNode:
    stale_runtime = bool(
        previous.execution_input_fingerprint
        and incoming.execution_input_fingerprint != previous.execution_input_fingerprint
    ) or bool(
        previous.selected_output_id
        and incoming.selected_output_id != previous.selected_output_id
    )
    outputs = incoming.outputs
    if stale_runtime:
        runtime_outputs = {
            key: value
            for key, value in previous.outputs.items()
            if key not in _CONFIG_OUTPUT_KEYS
        }
        config_outputs = {
            key: value
            for key, value in incoming.outputs.items()
            if key in _CONFIG_OUTPUT_KEYS
        }
        outputs = {**runtime_outputs, **config_outputs}
    return incoming.model_copy(
        update={
            "status": previous.status if stale_runtime else incoming.status,
            "outputs": outputs,
            "definition_version": max(
                previous.definition_version, incoming.definition_version
            ),
            "execution_input_fingerprint": previous.execution_input_fingerprint,
            "selected_output_id": previous.selected_output_id,
            "selected_output_url": previous.selected_output_url,
            "selected_output_reviewed_by": previous.selected_output_reviewed_by,
            "selected_output_reviewed_at": previous.selected_output_reviewed_at,
        }
    )


def merge_canvas_client_state(
    previous: ProductionCanvasSavedState | None,
    incoming: ProductionCanvasSavedState,
) -> ProductionCanvasSavedState:
    if previous is None:
        return incoming
    previous_by_id = {node.id: node for node in previous.nodes}
    return incoming.model_copy(
        update={
            "nodes": [
                (
                    _merge_client_node(previous_by_id[node.id], node)
                    if node.id in previous_by_id
                    else node
                )
                for node in incoming.nodes
            ]
        }
    )
