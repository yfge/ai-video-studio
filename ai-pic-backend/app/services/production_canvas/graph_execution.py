from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasSavedState,
)

from .run_context import (
    is_authoritative_canvas_context,
    merge_canvas_context_outputs,
    replace_canvas_context_outputs,
)


def apply_canvas_node_execution(
    state: ProductionCanvasSavedState,
    execution: ProductionCanvasNodeExecution,
) -> ProductionCanvasSavedState:
    if not execution.node_id:
        return state
    resolved = execution.resolved_context.model_dump(exclude_none=True)
    incoming = dict(execution.skill_result.outputs)
    if execution.task_id:
        incoming["task_id"] = execution.task_id
    nodes = [
        (
            node.model_copy(
                update={
                    "outputs": merge_canvas_context_outputs(
                        (
                            replace_canvas_context_outputs(node.outputs, resolved)
                            if is_authoritative_canvas_context(
                                execution.resolved_context
                            )
                            else merge_canvas_context_outputs(node.outputs, resolved)
                        ),
                        incoming,
                    ),
                    "status": execution.skill_result.status,
                    "execution_input_fingerprint": execution.input_fingerprint,
                }
            )
            if node.id == execution.node_id
            else node
        )
        for node in state.nodes
    ]
    return state.model_copy(update={"nodes": nodes})
