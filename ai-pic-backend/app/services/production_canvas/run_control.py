from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasRunActionRequest,
    ProductionCanvasRunActionResponse,
    ProductionCanvasRunResponse,
    ProductionCanvasSavedEdge,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteResponse,
)
from app.services.production_canvas.execution_persistence import (
    latest_canvas_execution_attempt,
    save_canvas_execution_response,
)
from app.services.production_canvas.executor import execute_canvas_resolution
from app.services.production_canvas.graph_runtime import (
    apply_canvas_node_execution,
    evaluate_canvas_graph,
    resolve_canvas_graph_request,
)
from app.services.production_canvas.run_cancellation import cancel_canvas_run
from app.services.production_canvas.run_persistence import load_canvas_skill_run
from app.services.production_canvas.run_requests import request_for_canvas_node
from sqlalchemy.orm import Session

from .access_control import require_canvas_access
from .collaboration import record_canvas_activity


def _run_and_state(
    db: Session, user: User, run_id: str
) -> tuple[ProductionCanvasRunResponse, ProductionCanvasSavedState]:
    run = load_canvas_skill_run(db, user, run_id)
    if run is None:
        raise ValueError("production_canvas_run_not_found")
    if run.saved_state is None or run.saved_state.graph_version != 2:
        raise ValueError("production_canvas_graph_not_executable")
    return run, run.saved_state


def _aggregate_execution(
    executions: list[ProductionCanvasNodeExecution],
    order: list[str],
) -> ProductionCanvasSkillExecuteResponse:
    first = executions[0]
    return ProductionCanvasSkillExecuteResponse(
        **first.model_dump(), execution_order=order, executions=executions
    )


def _eligible(action: str, node: ProductionCanvasSavedNode, status: str) -> bool:
    if node.kind in {"note", "skill_result"} or not node.skill:
        return False
    if action == "run_ready":
        return status == "ready" and node.status not in {"queued", "running"}
    return node.status in {"blocked", "cancelled", "failed", "stale"} or (
        status == "ready" and not node.execution_input_fingerprint
    )


def _execute_run_nodes(
    db: Session,
    user: User,
    run_id: str,
    action: str,
) -> ProductionCanvasRunActionResponse:
    run, state = _run_and_state(db, user, run_id)
    order = evaluate_canvas_graph(state).execution_order
    working = state
    executions: list[ProductionCanvasNodeExecution] = []
    attempted: list[str] = []
    for node_id in order:
        node = next((item for item in working.nodes if item.id == node_id), None)
        if node is None:
            continue
        evaluation = evaluate_canvas_graph(working)
        status = next(
            (item.status for item in evaluation.node_states if item.node_id == node_id),
            node.status,
        )
        if not _eligible(action, node, status):
            continue
        resolution = resolve_canvas_graph_request(
            working, request_for_canvas_node(run, node)
        )
        if resolution is None or resolution.missing_inputs:
            continue
        response = execute_canvas_resolution(db, user, resolution, working)
        execution = ProductionCanvasNodeExecution(**response.model_dump())
        attempted.append(node_id)
        executions.append(execution)
        working = apply_canvas_node_execution(working, execution)
    if executions:
        save_canvas_execution_response(
            db,
            user,
            run_id,
            _aggregate_execution(executions, attempted),
            definition_state=state,
        )
    refreshed = load_canvas_skill_run(db, user, run_id)
    assert refreshed is not None
    executable = [
        node.id
        for node in state.nodes
        if node.kind not in {"note", "skill_result"} and node.skill
    ]
    return ProductionCanvasRunActionResponse(
        action=action,
        run=refreshed,
        executions=executions,
        execution_order=attempted,
        skipped_node_ids=[
            node_id for node_id in executable if node_id not in attempted
        ],
    )


def _original_definition_state(
    state: ProductionCanvasSavedState,
    attempt: dict,
) -> ProductionCanvasSavedState:
    node = ProductionCanvasSavedNode.model_validate(attempt.get("definition_node"))
    incoming = [
        ProductionCanvasSavedEdge.model_validate(item)
        for item in attempt.get("incoming_edges") or []
    ]
    nodes = [node if item.id == node.id else item for item in state.nodes]
    edges = [edge for edge in state.edges if edge.to_node != node.id] + incoming
    return state.model_copy(update={"nodes": nodes, "edges": edges})


def _retry_node(
    db: Session,
    user: User,
    run_id: str,
    node_id: str | None,
    definition_mode: str,
) -> ProductionCanvasRunActionResponse:
    run, state = _run_and_state(db, user, run_id)
    node = next((item for item in state.nodes if item.id == node_id), None)
    if node is None or not node.skill:
        raise ValueError("production_canvas_node_not_found")
    definition_state = state
    if definition_mode == "original":
        attempt = latest_canvas_execution_attempt(db, user, run_id, node.id)
        if attempt is None or not attempt.get("definition_node"):
            raise ValueError("production_canvas_original_definition_unavailable")
        definition_state = _original_definition_state(state, attempt)
        node = next(item for item in definition_state.nodes if item.id == node.id)
    request = request_for_canvas_node(run, node)
    resolution = resolve_canvas_graph_request(definition_state, request)
    if resolution is None:
        raise ValueError("production_canvas_node_not_executable")
    response = execute_canvas_resolution(db, user, resolution, definition_state)
    save_canvas_execution_response(
        db,
        user,
        run_id,
        response,
        definition_state=definition_state,
        definition_mode=definition_mode,
    )
    refreshed = load_canvas_skill_run(db, user, run_id)
    assert refreshed is not None
    execution = ProductionCanvasNodeExecution(**response.model_dump())
    return ProductionCanvasRunActionResponse(
        action="retry",
        definition_mode=definition_mode,
        run=refreshed,
        executions=[execution],
        execution_order=[node.id],
    )


def control_canvas_run(
    db: Session,
    user: User,
    run_id: str,
    request: ProductionCanvasRunActionRequest,
) -> ProductionCanvasRunActionResponse:
    require_canvas_access(db, user, run_id, "execute")
    if request.action in {"run_ready", "resume"}:
        result = _execute_run_nodes(db, user, run_id, request.action)
    elif request.action == "retry":
        result = _retry_node(db, user, run_id, request.node_id, request.definition_mode)
    else:
        result = cancel_canvas_run(db, user, run_id)
    record_canvas_activity(
        db,
        user,
        run_id,
        f"run.{request.action}",
        target_type="node" if request.node_id else "run",
        target_id=request.node_id or run_id,
        detail=request.definition_mode if request.action == "retry" else None,
    )
    return result
