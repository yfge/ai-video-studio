import type {
  ProductionCanvasPlanNode,
  ProductionCanvasRunResponse,
  ProductionCanvasSavedNode,
  ProductionCanvasSavedState,
} from "@/utils/api/types";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  createProductionCanvasState,
  type ProductionCanvasState,
} from "./productionCanvasState";

function runOutputs(run: ProductionCanvasRunResponse) {
  return {
    ...(run.run_id ? { canvas_run_id: run.run_id } : {}),
    ...(run.task_id ? { canvas_task_id: run.task_id } : {}),
  };
}

function planNodeToCanvasNode(
  node: ProductionCanvasPlanNode,
  run: ProductionCanvasRunResponse,
): ProductionCanvasNode {
  return {
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height,
    kind: node.kind || "skill_result",
    skill: node.skill,
    detail: node.detail,
    outputs: { ...node.outputs, ...runOutputs(run) },
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
  };
}

function savedNodeToCanvasNode(node: ProductionCanvasSavedNode): ProductionCanvasNode {
  return {
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height || undefined,
    kind: node.kind || undefined,
    skill: node.skill || undefined,
    detail: node.detail || undefined,
    outputs: node.outputs,
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
  };
}

function canvasNodeToSavedNode(node: ProductionCanvasNode): ProductionCanvasSavedNode {
  return {
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height,
    kind: node.kind,
    skill: node.skill,
    detail: node.detail,
    outputs: node.outputs || {},
    reuse_targets: node.reuseTargets,
    action_href: node.actionHref,
    action_label: node.actionLabel,
  };
}

function savedEdges(edges?: { from: string; to: string }[] | null) {
  return Array.isArray(edges) ? edges.map((edge) => ({ ...edge })) : [];
}

function canvasEdgesToSavedEdges(edges: ProductionCanvasEdge[]) {
  return edges.map((edge) => ({ from: edge.from, to: edge.to }));
}

function selectedNodeId(nodes: ProductionCanvasNode[], requested?: string | null) {
  if (requested && nodes.some((node) => node.id === requested)) {
    return requested;
  }
  return nodes[0]?.id || "";
}

export function canvasRunIdFromNodes(nodes: ProductionCanvasNode[]) {
  for (const node of nodes) {
    const value = node.outputs?.canvas_run_id;
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

export function toProductionCanvasSavedState(
  state: ProductionCanvasState,
): ProductionCanvasSavedState {
  return {
    edges: canvasEdgesToSavedEdges(state.edges),
    nodes: state.nodes.map(canvasNodeToSavedNode),
    viewport: state.viewport,
    selected_node_id: state.selectedNodeId,
  };
}

export function productionCanvasStateFromRun(
  run: ProductionCanvasRunResponse,
): ProductionCanvasState {
  const saved = run.saved_state;
  if (saved?.nodes?.length) {
    const nodes = saved.nodes.map(savedNodeToCanvasNode);
    return {
      edges: savedEdges(saved.edges),
      nodes,
      viewport: saved.viewport,
      selectedNodeId: selectedNodeId(nodes, saved.selected_node_id),
    };
  }

  const nodes = run.nodes.map((node) => planNodeToCanvasNode(node, run));
  if (!nodes.length) return createProductionCanvasState();
  const state = createProductionCanvasState(nodes);
  return {
    ...state,
    selectedNodeId: selectedNodeId(state.nodes),
  };
}
