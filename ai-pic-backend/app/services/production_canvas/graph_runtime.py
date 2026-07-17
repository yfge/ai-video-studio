from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.schemas.production_canvas import (
    ProductionCanvasGraphEvaluation,
    ProductionCanvasGraphNodeState,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
)

from .graph_execution import apply_canvas_node_execution as apply_canvas_node_execution


@dataclass(frozen=True)
class CanvasGraphResolution:
    node_id: str
    request: ProductionCanvasSkillExecuteRequest
    resolved_inputs: dict[str, Any]
    missing_inputs: list[str]
    execution_order: list[str]


def _node_value(node: ProductionCanvasSavedNode, port_id: str, selected: bool):
    if node.status == "stale":
        return None
    outputs = node.outputs or {}
    if selected and node.selected_output_url:
        return node.selected_output_url
    if port_id in outputs:
        return outputs[port_id]
    aliases = {
        "production_brief": ("prompt",),
        "script": ("script_id",),
        "timeline": ("timeline_id",),
        "timeline_clip": ("clip_id",),
        "placed_timeline": ("timeline_id",),
        "execution": ("task_id", "dispatched_task_id"),
        "virtual_ip": ("virtual_ip_id", "virtual_ip_ids"),
        "environment": ("environment_id", "environment_ids"),
    }
    if selected:
        aliases = {
            **aliases,
            port_id: (
                "selected_output_id",
                "selected_output_url",
                "approved_asset_id",
                "output_url",
            ),
        }
    for key in aliases.get(port_id, ()):
        value = outputs.get(key)
        if value is not None and value != "" and value != []:
            return value
    return None


def _target_node(
    state: ProductionCanvasSavedState,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSavedNode | None:
    if request.node_id:
        return next((node for node in state.nodes if node.id == request.node_id), None)
    matches = [node for node in state.nodes if node.skill == request.skill]
    return matches[0] if len(matches) == 1 else None


def resolved_canvas_inputs(
    state: ProductionCanvasSavedState,
    target: ProductionCanvasSavedNode,
) -> tuple[dict[str, Any], list[str]]:
    node_by_id = {node.id: node for node in state.nodes}
    incoming = sorted(
        (edge for edge in state.edges if edge.to_node == target.id),
        key=lambda edge: edge.binding_order if edge.binding_order is not None else -1,
    )
    values: dict[str, Any] = {}
    for edge in incoming:
        source = node_by_id.get(edge.from_node)
        if source is None or not edge.from_port or not edge.to_port:
            continue
        value = _node_value(
            source,
            edge.from_port,
            edge.binding_type == "selected_output",
        )
        if value is None:
            continue
        target_port = next(
            (port for port in target.input_ports if port.id == edge.to_port),
            None,
        )
        if (
            target_port
            and target_port.type == "text"
            and edge.from_port == "production_brief"
            and isinstance(value, dict)
        ):
            value = (
                source.outputs.get("prompt")
                or value.get("source_prompt")
                or value.get("intent", {}).get(
                    "objective",
                )
            )
        if target_port and target_port.multiple:
            current = values.setdefault(edge.to_port, [])
            current.extend(value if isinstance(value, list) else [value])
        else:
            values[edge.to_port] = value
    missing = [
        port.id
        for port in target.input_ports
        if port.required and values.get(port.id) in (None, "", [])
    ]
    return values, missing


def _request_updates(values: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    production_context = values.get("production_context")
    if isinstance(production_context, dict):
        updates["production_context"] = production_context
    scalar_fields = {
        "shot_context": "prompt",
        "script": "script_id",
        "episode": "episode_id",
        "timeline": "timeline_id",
        "placed_timeline": "timeline_id",
        "timeline_clip": "clip_id",
        "virtual_ip": "virtual_ip_id",
        "environment": "environment_id",
        "execution": "task_id",
    }
    for port_id, field in scalar_fields.items():
        value = values.get(port_id)
        if isinstance(value, list) and value:
            value = value[0]
        if value is not None:
            updates[field] = value
    legacy_brief = values.get("production_brief")
    if isinstance(legacy_brief, str) and legacy_brief:
        updates["prompt"] = legacy_brief
    start_frame = values.get("start_frame")
    if isinstance(start_frame, list) and start_frame:
        start_frame = start_frame[0]
    if isinstance(start_frame, str) and start_frame:
        updates["start_frame_url"] = start_frame
    references: list[str] = []
    for port_id in ("start_frame", "storyboard_frame", "approved_storyboard"):
        value = values.get(port_id)
        items = value if isinstance(value, list) else [value]
        references.extend(item for item in items if isinstance(item, str) and item)
    if references:
        updates["reference_artifacts"] = list(dict.fromkeys(references))
    return updates


def _topological_order(
    state: ProductionCanvasSavedState,
    node_ids: set[str],
) -> list[str]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in state.edges:
        outgoing[edge.from_node].append(edge.to_node)
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in state.edges:
        if edge.from_node in node_ids and edge.to_node in node_ids:
            indegree[edge.to_node] += 1
    ready = [node.id for node in state.nodes if indegree.get(node.id) == 0]
    ordered: list[str] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for target_id in outgoing[node_id]:
            if target_id not in indegree:
                continue
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)
    return ordered


def _execution_order(state: ProductionCanvasSavedState, start_id: str) -> list[str]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in state.edges:
        outgoing[edge.from_node].append(edge.to_node)
    descendants = {start_id}
    stack = [start_id]
    while stack:
        for target_id in outgoing[stack.pop()]:
            if target_id not in descendants:
                descendants.add(target_id)
                stack.append(target_id)
    return _topological_order(state, descendants)


def resolve_canvas_graph_request(
    state: ProductionCanvasSavedState,
    request: ProductionCanvasSkillExecuteRequest,
) -> CanvasGraphResolution | None:
    if state.graph_version != 2:
        return None
    target = _target_node(state, request)
    if target is None:
        return None
    values, missing = resolved_canvas_inputs(state, target)
    resolved_request = request.model_copy(update=_request_updates(values))
    order = (
        _execution_order(state, target.id)
        if request.execution_scope == "downstream"
        else [target.id]
    )
    return CanvasGraphResolution(
        node_id=target.id,
        request=resolved_request,
        resolved_inputs=values,
        missing_inputs=missing,
        execution_order=order,
    )


def evaluate_canvas_graph(
    state: ProductionCanvasSavedState,
) -> ProductionCanvasGraphEvaluation:
    node_states: list[ProductionCanvasGraphNodeState] = []
    for node in state.nodes:
        _, missing = resolved_canvas_inputs(state, node)
        status = node.status
        if node.kind != "note" and status in {"draft", "ready", "blocked"}:
            status = "draft" if missing else "ready"
        node_states.append(
            ProductionCanvasGraphNodeState(
                node_id=node.id,
                status=status,
                missing_inputs=missing,
            )
        )
    order = _topological_order(state, {node.id for node in state.nodes})
    return ProductionCanvasGraphEvaluation(
        graph_version=state.graph_version,
        node_states=node_states,
        execution_order=order,
    )
