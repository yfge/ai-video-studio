import type {
  ProductionCanvasRunResponse,
  ProductionCanvasSavedNode,
  ProductionCanvasSavedState,
} from "@/utils/api/types";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  clampProductionCanvasZoom,
  finiteCanvasNumber,
} from "./productionCanvasGeometry";
import {
  planNodeToCanvasNode,
  restoredSavedNode,
} from "./productionCanvasRunNodes";
import {
  createProductionCanvasState,
  type ProductionCanvasState,
} from "./productionCanvasState";
import { reconcileProductionCanvasExecutionTasks } from "./productionCanvasExecutionTracking";

function canvasNodeToSavedNode(
  node: ProductionCanvasNode,
): ProductionCanvasSavedNode {
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

function selectedNodeId(
  nodes: ProductionCanvasNode[],
  requested?: string | null,
) {
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
    const fallback = createProductionCanvasState();
    const planNodesById = new Map(run.nodes.map((node) => [node.id, node]));
    const nodes = saved.nodes
      .map((node) => restoredSavedNode(node, run, planNodesById))
      .filter((node): node is ProductionCanvasNode => Boolean(node));
    const restoredIds = new Set(nodes.map((node) => node.id));
    nodes.push(
      ...run.nodes
        .filter((node) => !restoredIds.has(node.id))
        .map((node) => planNodeToCanvasNode(node, run)),
    );
    const restored = createProductionCanvasState(
      reconcileProductionCanvasExecutionTasks(nodes),
      savedEdges(saved.edges),
    );
    return {
      ...restored,
      viewport: {
        x: finiteCanvasNumber(saved.viewport?.x, fallback.viewport.x),
        y: finiteCanvasNumber(saved.viewport?.y, fallback.viewport.y),
        zoom: clampProductionCanvasZoom(
          saved.viewport?.zoom,
          fallback.viewport.zoom,
        ),
      },
      selectedNodeId: selectedNodeId(restored.nodes, saved.selected_node_id),
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
