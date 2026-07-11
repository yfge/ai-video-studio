import type { RefObject } from "react";
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
import { useProductionCanvasSelectionActions } from "./useProductionCanvasSelectionActions";
import { insertProductionCanvasTemplate } from "./productionCanvasTemplates";

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
  const appendNodes = (nodes: ProductionCanvasNode[]) => {
    if (!nodes.length) return;
    setCanvasDefinition((state) => {
      const incomingIds = new Set(nodes.map((node) => node.id));
      const selectedNodeId = nodes[0]?.id || state.selectedNodeId;
      return {
        ...state,
        nodes: applyProductionCanvasContext([
          ...state.nodes.filter((node) => !incomingIds.has(node.id)),
          ...nodes,
        ]),
        selectedNodeId,
        selectedNodeIds: [selectedNodeId],
      };
    });
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
