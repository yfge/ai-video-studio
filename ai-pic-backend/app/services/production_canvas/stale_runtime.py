from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from app.schemas.production_canvas import (
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
)
from app.schemas.production_canvas_review import ProductionCanvasStaleImpactNode
from app.services.production_canvas.graph_runtime import resolved_canvas_inputs


def canvas_node_input_fingerprint(
    state: ProductionCanvasSavedState,
    node_id: str,
) -> str | None:
    node = next((item for item in state.nodes if item.id == node_id), None)
    if node is None or node.kind == "note":
        return None
    values, _ = resolved_canvas_inputs(state, node)
    edges = sorted(
        (
            {
                "edge_id": edge.edge_id,
                "from": edge.from_node,
                "from_port": edge.from_port,
                "to_port": edge.to_port,
                "binding_type": edge.binding_type,
                "binding_order": edge.binding_order,
            }
            for edge in state.edges
            if edge.to_node == node_id
        ),
        key=lambda item: (item["binding_order"] or -1, item["edge_id"] or ""),
    )
    payload = {
        "definition_version": node.definition_version,
        "edges": edges,
        "resolved_inputs": values,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def _stale_descendants(state: ProductionCanvasSavedState, seeds: set[str]) -> set[str]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in state.edges:
        outgoing[edge.from_node].append(edge.to_node)
    stale = set(seeds)
    stack = list(seeds)
    while stack:
        for node_id in outgoing[stack.pop()]:
            if node_id not in stale:
                stale.add(node_id)
                stack.append(node_id)
    return stale


def canvas_stale_descendant_ids(
    state: ProductionCanvasSavedState, node_id: str
) -> list[str]:
    stale = _stale_descendants(state, {node_id}) - {node_id}
    return [node.id for node in state.nodes if node.id in stale and node.kind != "note"]


def canvas_stale_impact_nodes(
    state: ProductionCanvasSavedState, node_id: str
) -> list[ProductionCanvasStaleImpactNode]:
    stale = set(canvas_stale_descendant_ids(state, node_id))
    return [
        ProductionCanvasStaleImpactNode(node_id=node.id, title=node.label)
        for node in state.nodes
        if node.id in stale and node.execution_input_fingerprint
    ]


def apply_canvas_stale_state(
    previous: ProductionCanvasSavedState | None,
    incoming: ProductionCanvasSavedState,
) -> ProductionCanvasSavedState:
    if incoming.graph_version != 2 or previous is None:
        return incoming
    previous_by_id = {node.id: node for node in previous.nodes}
    nodes: list[ProductionCanvasSavedNode] = []
    for node in incoming.nodes:
        old = previous_by_id.get(node.id)
        fingerprint = node.execution_input_fingerprint or (
            old.execution_input_fingerprint if old else None
        )
        nodes.append(
            node.model_copy(update={"execution_input_fingerprint": fingerprint})
        )
    state = incoming.model_copy(update={"nodes": nodes})
    seeds = {
        node.id
        for node in state.nodes
        if node.execution_input_fingerprint
        and canvas_node_input_fingerprint(state, node.id)
        != node.execution_input_fingerprint
    }
    stale = _stale_descendants(state, seeds)
    return state.model_copy(
        update={
            "nodes": [
                (
                    node.model_copy(update={"status": "stale"})
                    if node.id in stale and node.kind != "note"
                    else node
                )
                for node in state.nodes
            ]
        }
    )
