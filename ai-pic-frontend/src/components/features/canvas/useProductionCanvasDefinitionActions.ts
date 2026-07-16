import type { RefObject } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  addProductionCanvasEdge,
  removeProductionCanvasEdge,
  updateProductionCanvasNode,
  updateProductionCanvasNodeOutputs,
  type ProductionCanvasOutputPatch,
} from "./productionCanvasGraphState";
import {
  addProductionCanvasNote,
  applyProductionCanvasContext,
} from "./productionCanvasState";
import {
  removeProductionCanvasSectionNode,
  toggleProductionCanvasSection,
} from "./productionCanvasSections";
import type { ProductionCanvasDefinitionSetter } from "./useProductionCanvasHistory";
import type { ProductionCanvasState } from "./productionCanvasState";
import { useProductionCanvasSelectionActions } from "./useProductionCanvasSelectionActions";
import { insertProductionCanvasTemplate } from "./productionCanvasTemplates";
import {
  isProductionCanvasPlanBatch,
  productionCanvasPlanEdges,
  withoutProductionCanvasPlaceholders,
} from "./productionCanvasPlanGraph";

function withoutPlannedEdges(node: ProductionCanvasNode) {
  const incoming = { ...node };
  delete incoming.plannedEdges;
  return incoming;
}

export function appendProductionCanvasNodes(
  state: ProductionCanvasState,
  nodes: ProductionCanvasNode[],
  resolvedContext?: ProductionCanvasResolvedContext,
): ProductionCanvasState {
  if (!nodes.length) return state;
  const plannedEdges = nodes.find((node) => node.plannedEdges !== undefined)
    ?.plannedEdges;
  const incomingNodes = nodes.map(withoutPlannedEdges);
  const isPlan =
    plannedEdges !== undefined || isProductionCanvasPlanBatch(incomingNodes);
  const incomingIds = new Set(incomingNodes.map((node) => node.id));
  const retainedNodes = (
    isPlan ? withoutProductionCanvasPlaceholders(state.nodes) : state.nodes
  ).filter((node) => !incomingIds.has(node.id));
  const mergedNodes = [...retainedNodes, ...incomingNodes];
  const mergedNodeIds = new Set(mergedNodes.map((node) => node.id));
  const retainedEdges = state.edges.filter(
    (edge) =>
      mergedNodeIds.has(edge.from) &&
      mergedNodeIds.has(edge.to) &&
      !incomingIds.has(edge.from) &&
      !incomingIds.has(edge.to),
  );
  const taskPublication = incomingNodes.some(
    (node) =>
      node.kind === "note" &&
      typeof node.outputs?.source_node_id === "string" &&
      (typeof node.outputs?.task_id === "number" ||
        typeof node.outputs?.render_job_id === "number"),
  );
  const selectedNodeId =
    taskPublication && mergedNodeIds.has(state.selectedNodeId)
      ? state.selectedNodeId
      : incomingNodes[0]?.id || state.selectedNodeId;
  const incomingContextRevision = Math.max(
    0,
    ...incomingNodes.map((node) =>
      typeof node.outputs?.resolved_context_revision === "number"
        ? node.outputs.resolved_context_revision
        : 0,
    ),
  );
  return {
    ...state,
    nodes: applyProductionCanvasContext(mergedNodes, resolvedContext),
    edges: isPlan
      ? [
          ...retainedEdges,
          ...(plannedEdges || productionCanvasPlanEdges(incomingNodes)),
        ]
      : state.edges,
    sections: (state.sections || []).map((section) => ({
      ...section,
      nodeIds: section.nodeIds.filter((nodeId) => mergedNodeIds.has(nodeId)),
    })),
    selectedNodeId,
    selectedNodeIds: [selectedNodeId],
    resolvedContextRevision: Math.max(
      state.resolvedContextRevision || 0,
      incomingContextRevision,
    ),
  };
}

export function useProductionCanvasDefinitionActions({
  canvasRef,
  setCanvasDefinition,
}: {
  canvasRef: RefObject<HTMLDivElement | null>;
  setCanvasDefinition: ProductionCanvasDefinitionSetter;
}) {
  const selectionActions = useProductionCanvasSelectionActions((action) =>
    setCanvasDefinition(action),
  );
  const handleAddEdge = (edge: ProductionCanvasEdge) =>
    setCanvasDefinition((state) => ({
      ...state,
      edges: addProductionCanvasEdge(state.edges, edge),
    }));
  const handleRemoveEdge = (edge: ProductionCanvasEdge) =>
    setCanvasDefinition((state) => ({
      ...state,
      edges: removeProductionCanvasEdge(state.edges, edge),
    }));
  const handleRemoveNode = (nodeId: string) =>
    setCanvasDefinition((state) =>
      removeProductionCanvasSectionNode(state, nodeId),
    );
  const handleUpdateNodeOutputs = (
    nodeId: string,
    patch: ProductionCanvasOutputPatch,
  ) =>
    setCanvasDefinition((state) => ({
      ...state,
      nodes: updateProductionCanvasNodeOutputs(state.nodes, nodeId, patch),
    }));
  const handleUpdateNode = (
    nodeId: string,
    patch: Partial<ProductionCanvasNode>,
  ) =>
    setCanvasDefinition((state) => ({
      ...state,
      nodes: updateProductionCanvasNode(state.nodes, nodeId, patch),
    }));
  const handleToggleSection = (sectionId: string) =>
    setCanvasDefinition((state) =>
      toggleProductionCanvasSection(state, sectionId),
    );
  const handleAddNote = (targetPosition?: { x: number; y: number }) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    setCanvasDefinition((state) => {
      const position = targetPosition || {
        x:
          ((rect?.width || 720) / 2 - state.viewport.x) / state.viewport.zoom -
          95,
        y:
          ((rect?.height || 420) / 2 - state.viewport.y) / state.viewport.zoom -
          48,
      };
      const noteIndex =
        state.nodes.filter((node) => node.kind === "note").length + 1;
      const nodes = addProductionCanvasNote(state.nodes, noteIndex, position);
      const selectedNodeId =
        nodes[nodes.length - 1]?.id || state.selectedNodeId;
      return {
        ...state,
        nodes,
        selectedNodeId,
        selectedNodeIds: [selectedNodeId],
      };
    });
    canvasRef.current?.focus({ preventScroll: true });
  };
  const appendNodes = (
    nodes: ProductionCanvasNode[],
    resolvedContext?: ProductionCanvasResolvedContext,
  ) => {
    if (!nodes.length) return;
    setCanvasDefinition((state) =>
      appendProductionCanvasNodes(state, nodes, resolvedContext),
    );
  };
  const handleInsertTemplate = (templateId: string) => {
    setCanvasDefinition((state) =>
      insertProductionCanvasTemplate(state, templateId),
    );
    canvasRef.current?.focus({ preventScroll: true });
  };

  return {
    appendNodes,
    handleAddEdge,
    handleAddNote,
    handleInsertTemplate,
    handleRemoveEdge,
    handleRemoveNode,
    handleToggleSection,
    handleUpdateNode,
    handleUpdateNodeOutputs,
    selectionActions,
  };
}
