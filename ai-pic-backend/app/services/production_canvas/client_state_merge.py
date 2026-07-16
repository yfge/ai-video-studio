from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
)
from app.services.production_canvas.run_context import (
    canvas_run_context,
    merge_canvas_node_context_outputs,
)

_CONFIG_OUTPUT_KEYS = {
    "aspect_ratio",
    "camera_fixed",
    "duration",
    "fps",
    "frame_indexes",
    "media_model",
    "model",
    "prompt",
    "ratio",
    "require_reference_images",
    "resolution",
    "video_aspect_ratio",
    "video_duration",
    "video_fps",
    "video_resolution",
}

_TASK_ID_KEYS = ("task_id", "dispatched_task_id", "canvas_task_id")
_TASK_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
_RENDER_TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def _runtime_id(outputs: dict, keys: tuple[str, ...]):
    return next((outputs.get(key) for key in keys if outputs.get(key)), None)


def _terminal_runtime_regressed(
    previous: ProductionCanvasSavedNode, incoming: ProductionCanvasSavedNode
) -> bool:
    checks = (
        (_TASK_ID_KEYS, "task_status", _TASK_TERMINAL_STATUSES),
        (("render_job_id",), "render_status", _RENDER_TERMINAL_STATUSES),
    )
    for id_keys, status_key, terminal_statuses in checks:
        previous_id = _runtime_id(previous.outputs, id_keys)
        incoming_id = _runtime_id(incoming.outputs, id_keys)
        if not previous_id or previous_id != incoming_id:
            continue
        if (
            previous.outputs.get(status_key) in terminal_statuses
            and incoming.outputs.get(status_key) not in terminal_statuses
        ):
            return True
    return False


def _runtime_managed_node(node: ProductionCanvasSavedNode) -> bool:
    if node.kind != "note":
        return True
    outputs = node.outputs
    return bool(
        outputs.get("source_node_id")
        and (
            _runtime_id(outputs, _TASK_ID_KEYS)
            or _runtime_id(outputs, ("render_job_id",))
        )
    )


def _has_stale_runtime(
    previous: ProductionCanvasSavedNode, incoming: ProductionCanvasSavedNode
) -> bool:
    return (
        incoming.definition_version < previous.definition_version
        or bool(
            previous.execution_input_fingerprint
            and incoming.execution_input_fingerprint
            != previous.execution_input_fingerprint
        )
        or bool(
            previous.selected_output_id
            and incoming.selected_output_id != previous.selected_output_id
        )
        or _terminal_runtime_regressed(previous, incoming)
    )


def _merge_client_node(
    previous: ProductionCanvasSavedNode,
    incoming: ProductionCanvasSavedNode,
) -> ProductionCanvasSavedNode:
    stale_runtime = _has_stale_runtime(previous, incoming)
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


def canvas_client_state_has_stale_runtime(
    previous: ProductionCanvasSavedState | None,
    incoming: ProductionCanvasSavedState,
) -> bool:
    if previous is None:
        return False
    incoming_by_id = {node.id: node for node in incoming.nodes}
    return any(
        (
            _has_stale_runtime(node, incoming_by_id[node.id])
            if node.id in incoming_by_id
            else True
        )
        for node in previous.nodes
        if _runtime_managed_node(node)
    )


def merge_canvas_client_state(
    previous: ProductionCanvasSavedState | None,
    incoming: ProductionCanvasSavedState,
    authoritative_context: dict | None = None,
) -> ProductionCanvasSavedState:
    if previous is None:
        if authoritative_context is None:
            return incoming
        return incoming.model_copy(
            update={
                "nodes": [
                    (
                        node
                        if node.kind == "note"
                        else node.model_copy(
                            update={
                                "outputs": merge_canvas_node_context_outputs(
                                    {"skill": node.skill, "outputs": node.outputs},
                                    authoritative_context,
                                    authoritative=True,
                                )
                            }
                        )
                    )
                    for node in incoming.nodes
                ]
            }
        )
    previous_by_id = {node.id: node for node in previous.nodes}
    preserve_context = (
        authoritative_context is not None
        or canvas_client_state_has_stale_runtime(previous, incoming)
    )
    nodes = [
        (
            _merge_client_node(previous_by_id[node.id], node)
            if node.id in previous_by_id
            else (
                node.model_copy(
                    update={
                        "outputs": merge_canvas_node_context_outputs(
                            {"skill": node.skill, "outputs": node.outputs},
                            authoritative_context,
                            authoritative=True,
                        )
                    }
                )
                if authoritative_context is not None and node.kind != "note"
                else node
            )
        )
        for node in incoming.nodes
    ]
    if preserve_context:
        context = canvas_run_context(
            {"resolved_context": authoritative_context}
            if authoritative_context is not None
            else {"saved_state": previous.model_dump(mode="json")}
        )
        nodes = [
            (
                node
                if node.kind == "note"
                else node.model_copy(
                    update={
                        "outputs": merge_canvas_node_context_outputs(
                            {"skill": node.skill, "outputs": node.outputs},
                            context,
                            authoritative=True,
                        )
                    }
                )
            )
            for node in nodes
        ]
    return incoming.model_copy(update={"nodes": nodes})
