import type {
  ProductionCanvasRunResponse,
  ProductionCanvasSavedNode,
  ProductionCanvasSavedState,
} from "@/utils/api/types";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import { isTypedProductionCanvasEdge } from "./productionCanvasPorts";
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
    kind: node.skill ? "pipeline" : node.kind,
    skill: node.skill,
    detail: node.detail,
    outputs: node.outputs || {},
    reuse_targets: node.reuseTargets,
    action_href: node.actionHref,
    action_label: node.actionLabel,
    definition_version: node.definitionVersion || 1,
    execution_input_fingerprint: node.executionInputFingerprint,
    input_ports: node.inputPorts?.map(({ id, type, required, multiple }) => ({
      id,
      type,
      required,
      multiple,
    })),
    output_ports: node.outputPorts?.map(({ id, type, required, multiple }) => ({
      id,
      type,
      required,
      multiple,
    })),
  };
}

function savedEdges(
  edges?: ProductionCanvasSavedState["edges"] | null,
): ProductionCanvasEdge[] {
  return Array.isArray(edges)
    ? edges.map((edge) => ({
        from: edge.from,
        to: edge.to,
        ...(edge.edge_id ? { edgeId: edge.edge_id } : {}),
        ...(edge.from_port ? { fromPort: edge.from_port } : {}),
        ...(edge.to_port ? { toPort: edge.to_port } : {}),
        ...(edge.binding_type ? { bindingType: edge.binding_type } : {}),
        ...(edge.required === undefined ? {} : { required: edge.required }),
        ...(edge.binding_order === undefined || edge.binding_order === null
          ? {}
          : { bindingOrder: edge.binding_order }),
      }))
    : [];
}

function canvasEdgesToSavedEdges(edges: ProductionCanvasEdge[]) {
  return edges.map((edge) => ({
    from: edge.from,
    to: edge.to,
    edge_id: edge.edgeId,
    from_port: edge.fromPort,
    to_port: edge.toPort,
    binding_type: edge.bindingType,
    required: edge.required ?? true,
    binding_order: edge.bindingOrder,
  }));
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
    graph_version: state.edges.every(isTypedProductionCanvasEdge) ? 2 : 1,
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
