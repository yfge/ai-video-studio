import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import type { ProductionCanvasState } from "./productionCanvasState";
import { productionCanvasDefinitionOutputs } from "./productionCanvasDefinition";

export type ProductionCanvasAlignment =
  | "left"
  | "top"
  | "distribute-x"
  | "distribute-y";

export function selectedProductionCanvasNodeIds(state: ProductionCanvasState) {
  const requested = state.selectedNodeIds?.length
    ? state.selectedNodeIds
    : state.selectedNodeId
    ? [state.selectedNodeId]
    : [];
  const existing = new Set(state.nodes.map((node) => node.id));
  return Array.from(new Set(requested)).filter((id) => existing.has(id));
}

export function selectProductionCanvasNode(
  state: ProductionCanvasState,
  nodeId: string,
  additive = false,
): ProductionCanvasState {
  if (!nodeId) {
    return { ...state, selectedNodeId: "", selectedNodeIds: [] };
  }
  if (!state.nodes.some((node) => node.id === nodeId)) return state;
  const selected = selectedProductionCanvasNodeIds(state);
  if (!additive) {
    return { ...state, selectedNodeId: nodeId, selectedNodeIds: [nodeId] };
  }
  const next = selected.includes(nodeId)
    ? selected.filter((id) => id !== nodeId)
    : [...selected, nodeId];
  return {
    ...state,
    selectedNodeId: next.includes(nodeId)
      ? nodeId
      : next[next.length - 1] || "",
    selectedNodeIds: next,
  };
}

export function moveProductionCanvasNodes(
  nodes: ProductionCanvasNode[],
  nodeIds: string[],
  dx: number,
  dy: number,
) {
  const selected = new Set(nodeIds);
  return nodes.map((node) =>
    selected.has(node.id)
      ? { ...node, x: Math.round(node.x + dx), y: Math.round(node.y + dy) }
      : node,
  );
}

export function alignProductionCanvasSelection(
  state: ProductionCanvasState,
  alignment: ProductionCanvasAlignment,
): ProductionCanvasState {
  const selected = new Set(selectedProductionCanvasNodeIds(state));
  const nodes = state.nodes.filter((node) => selected.has(node.id));
  if (nodes.length < 2) return state;
  if (alignment === "left") {
    const x = Math.min(...nodes.map((node) => node.x));
    return {
      ...state,
      nodes: state.nodes.map((node) =>
        selected.has(node.id) ? { ...node, x } : node,
      ),
    };
  }
  if (alignment === "top") {
    const y = Math.min(...nodes.map((node) => node.y));
    return {
      ...state,
      nodes: state.nodes.map((node) =>
        selected.has(node.id) ? { ...node, y } : node,
      ),
    };
  }
  if (nodes.length < 3) return state;
  const axis = alignment === "distribute-x" ? "x" : "y";
  const sorted = [...nodes].sort((left, right) => left[axis] - right[axis]);
  const first = sorted[0]?.[axis] || 0;
  const last = sorted[sorted.length - 1]?.[axis] || first;
  const step = (last - first) / (sorted.length - 1);
  const positions = new Map(
    sorted.map((node, index) => [node.id, Math.round(first + step * index)]),
  );
  return {
    ...state,
    nodes: state.nodes.map((node) =>
      positions.has(node.id)
        ? { ...node, [axis]: positions.get(node.id) }
        : node,
    ),
  };
}

function copyId(nodes: ProductionCanvasNode[], sourceId: string) {
  let index = 1;
  while (nodes.some((node) => node.id === `${sourceId}-copy-${index}`)) {
    index += 1;
  }
  return `${sourceId}-copy-${index}`;
}

function copiedEdge(
  edge: ProductionCanvasEdge,
  copiedIds: Map<string, string>,
): ProductionCanvasEdge {
  const from = copiedIds.get(edge.from) || edge.from;
  const to = copiedIds.get(edge.to) || edge.to;
  return {
    ...edge,
    from,
    to,
    edgeId:
      edge.fromPort && edge.toPort
        ? `${from}-${edge.fromPort}-to-${to}-${edge.toPort}`
        : undefined,
  };
}

export function duplicateProductionCanvasSelection(
  state: ProductionCanvasState,
): ProductionCanvasState {
  const selected = new Set(selectedProductionCanvasNodeIds(state));
  const sources = state.nodes.filter(
    (node) => selected.has(node.id) && node.kind !== "note",
  );
  if (!sources.length) return state;
  const copiedIds = new Map<string, string>();
  const allNodes = [...state.nodes];
  const copies = sources.map((node) => {
    const id = copyId(allNodes, node.id);
    copiedIds.set(node.id, id);
    const copy: ProductionCanvasNode = {
      ...node,
      id,
      status: "draft",
      x: node.x + 32,
      y: node.y + 32,
      outputs: productionCanvasDefinitionOutputs(node.outputs),
      definitionVersion: 1,
      executionInputFingerprint: undefined,
      selectedOutputId: undefined,
      selectedOutputUrl: undefined,
      selectedOutputReviewedBy: undefined,
      selectedOutputReviewedAt: undefined,
    };
    allNodes.push(copy);
    return copy;
  });
  const copiedEdges = state.edges
    .filter((edge) => selected.has(edge.from) && selected.has(edge.to))
    .map((edge) => copiedEdge(edge, copiedIds));
  return {
    ...state,
    nodes: [...state.nodes, ...copies],
    edges: [...state.edges, ...copiedEdges],
    selectedNodeId: copies[0]?.id || state.selectedNodeId,
    selectedNodeIds: copies.map((node) => node.id),
  };
}
