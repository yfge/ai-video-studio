from __future__ import annotations

from collections import defaultdict
from typing import Any


def _reject_cycles(node_ids: set[str], edges: list[Any]) -> None:
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = dict.fromkeys(node_ids, 0)
    for edge in edges:
        outgoing[edge.from_node].append(edge.to_node)
        indegree[edge.to_node] += 1

    ready = [node_id for node_id, count in indegree.items() if count == 0]
    visited = 0
    while ready:
        node_id = ready.pop()
        visited += 1
        for target_id in outgoing[node_id]:
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)
    if visited != len(node_ids):
        raise ValueError("Executable canvas graph cannot contain cycles")


def _validate_sections(state: Any, node_ids: set[str]) -> None:
    section_ids: set[str] = set()
    for section in state.sections:
        if section.id in section_ids:
            raise ValueError(f"Canvas section ids must be unique: {section.id}")
        section_ids.add(section.id)
        if len(section.node_ids) != len(set(section.node_ids)):
            raise ValueError(f"Canvas section members must be unique: {section.id}")
        if not set(section.node_ids).issubset(node_ids):
            raise ValueError(f"Canvas section references an unknown node: {section.id}")


def validate_saved_graph(state: Any) -> None:
    node_by_id = {node.id: node for node in state.nodes}
    if len(node_by_id) != len(state.nodes):
        raise ValueError("Canvas node ids must be unique")
    _validate_sections(state, set(node_by_id))
    if state.graph_version == 1:
        return

    for node in state.nodes:
        input_ids = [port.id for port in node.input_ports]
        output_ids = [port.id for port in node.output_ports]
        if len(set(input_ids)) != len(input_ids):
            raise ValueError(f"Canvas input port ids must be unique: {node.id}")
        if len(set(output_ids)) != len(output_ids):
            raise ValueError(f"Canvas output port ids must be unique: {node.id}")

    edge_ids: set[str] = set()
    bindings: set[tuple[str, str, str, str]] = set()
    single_inputs: set[tuple[str, str]] = set()
    ordered_inputs: set[tuple[str, str, int]] = set()
    for edge in state.edges:
        if not edge.edge_id or not edge.from_port or not edge.to_port:
            raise ValueError(
                "Typed canvas edges require edge_id, from_port, and to_port"
            )
        if edge.binding_type is None:
            raise ValueError("Typed canvas edges require binding_type")
        if edge.edge_id in edge_ids:
            raise ValueError(f"Duplicate canvas edge id: {edge.edge_id}")
        edge_ids.add(edge.edge_id)
        binding = (edge.from_node, edge.from_port, edge.to_node, edge.to_port)
        if binding in bindings:
            raise ValueError("Duplicate canvas edge binding")
        bindings.add(binding)

        source = node_by_id.get(edge.from_node)
        target = node_by_id.get(edge.to_node)
        if source is None or target is None:
            raise ValueError("Canvas edge references an unknown node")
        if source.id == target.id:
            raise ValueError("Canvas executable edges cannot be self-referential")
        if source.kind == "note" or target.kind in {"note", "skill_result"}:
            raise ValueError(
                "Notes and task evidence cannot be executable edge targets"
            )

        source_ports = {port.id: port for port in source.output_ports}
        target_ports = {port.id: port for port in target.input_ports}
        source_port = source_ports.get(edge.from_port)
        target_port = target_ports.get(edge.to_port)
        if source_port is None or target_port is None:
            raise ValueError("Canvas edge references an unknown port")
        if source_port.type != target_port.type:
            raise ValueError(
                f"Incompatible canvas port types: {source_port.type} -> {target_port.type}"
            )
        target_key = (target.id, target_port.id)
        if not target_port.multiple and target_key in single_inputs:
            raise ValueError("Single-value canvas input accepts only one binding")
        if target_port.multiple:
            if edge.binding_order is None:
                raise ValueError("Multi-value canvas bindings require binding_order")
            ordered_key = (*target_key, edge.binding_order)
            if ordered_key in ordered_inputs:
                raise ValueError("Multi-value canvas binding_order must be unique")
            ordered_inputs.add(ordered_key)
        single_inputs.add(target_key)

    _reject_cycles(set(node_by_id), state.edges)
