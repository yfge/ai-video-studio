import { useEffect, useMemo, useRef, useState } from "react";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  addProductionCanvasEdge,
  removeProductionCanvasEdge,
  removeProductionCanvasNode,
  updateProductionCanvasNode,
  updateProductionCanvasNodeOutputs,
  type ProductionCanvasOutputPatch,
} from "./productionCanvasGraphState";
import {
  addProductionCanvasNote,
  applyProductionCanvasContext,
  createProductionCanvasState,
} from "./productionCanvasState";
import {
  CANVAS_BASE_HEIGHT,
  CANVAS_BASE_WIDTH,
  centerProductionCanvasOnNode,
  getWorldBounds,
  readStoredCanvasState,
} from "./productionCanvasViewModel";
import { useProductionCanvasInteractionControls } from "./useProductionCanvasInteractionControls";
import { useProductionCanvasKeyboardCommands } from "./useProductionCanvasKeyboardCommands";
import {
  selectProductionCanvasNode,
  selectedProductionCanvasNodeIds,
} from "./productionCanvasSelection";
import { useProductionCanvasSelectionActions } from "./useProductionCanvasSelectionActions";

export function useProductionCanvasController(storageKey?: string | null) {
  const [canvasState, setCanvasState] = useState(createProductionCanvasState);
  const [storageLoaded, setStorageLoaded] = useState(storageKey === null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const worldBounds = useMemo(
    () => getWorldBounds(canvasState.nodes),
    [canvasState.nodes],
  );
  const selectedNode = canvasState.nodes.find(
    (node) => node.id === canvasState.selectedNodeId,
  );
  const selectionActions = useProductionCanvasSelectionActions(setCanvasState);
  const zoomLabel = `${Math.round(canvasState.viewport.zoom * 100)}%`;
  const {
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleNodePointerDown,
    handleZoomButton,
  } = useProductionCanvasInteractionControls({
    canvasRef,
    canvasState,
    setCanvasState,
  });

  useEffect(() => {
    setCanvasState(readStoredCanvasState(storageKey));
    setStorageLoaded(true);
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey || !storageLoaded || typeof window === "undefined") return;
    window.localStorage.setItem(storageKey, JSON.stringify(canvasState));
  }, [canvasState, storageKey, storageLoaded]);

  const handleSelectNode = (nodeId: string, additive = false) =>
    setCanvasState((state) =>
      selectProductionCanvasNode(state, nodeId, additive),
    );

  const handleAddEdge = (edge: ProductionCanvasEdge) =>
    setCanvasState((state) => ({
      ...state,
      edges: addProductionCanvasEdge(state.edges, edge),
    }));
  const handleRemoveEdge = (edge: ProductionCanvasEdge) =>
    setCanvasState((state) => ({
      ...state,
      edges: removeProductionCanvasEdge(state.edges, edge),
    }));
  const handleRemoveNode = (nodeId: string) => {
    setCanvasState((state) => {
      const next = removeProductionCanvasNode(state.nodes, state.edges, nodeId);
      return {
        ...state,
        ...next,
        selectedNodeId:
          state.selectedNodeId === nodeId
            ? next.nodes[0]?.id || ""
            : state.selectedNodeId,
        selectedNodeIds: selectedProductionCanvasNodeIds(state).filter(
          (id) => id !== nodeId,
        ),
      };
    });
  };
  const handleUpdateNodeOutputs = (
    nodeId: string,
    patch: ProductionCanvasOutputPatch,
  ) =>
    setCanvasState((state) => ({
      ...state,
      nodes: updateProductionCanvasNodeOutputs(state.nodes, nodeId, patch),
    }));

  const handleUpdateNode = (
    nodeId: string,
    patch: Partial<ProductionCanvasNode>,
  ) =>
    setCanvasState((state) => ({
      ...state,
      nodes: updateProductionCanvasNode(state.nodes, nodeId, patch),
    }));

  const handleReset = () => {
    setCanvasState(createProductionCanvasState());
    if (storageKey && typeof window !== "undefined") {
      window.localStorage.removeItem(storageKey);
    }
  };

  const handleFocusSelectedNode = (nodeId?: string) => {
    const width = canvasRef.current?.clientWidth || CANVAS_BASE_WIDTH;
    const height = canvasRef.current?.clientHeight || CANVAS_BASE_HEIGHT;
    setCanvasState((state) => {
      const targetNodeId = nodeId || state.selectedNodeId;
      const node = targetNodeId
        ? state.nodes.find((item) => item.id === targetNodeId)
        : undefined;
      if (!node) return state;
      return {
        ...state,
        selectedNodeId: node.id,
        selectedNodeIds: [node.id],
        viewport: centerProductionCanvasOnNode(state.viewport, node, {
          width,
          height,
        }),
      };
    });
    canvasRef.current?.focus({ preventScroll: true });
  };

  const handleNavigate = (point: { x: number; y: number }) => {
    const width = canvasRef.current?.clientWidth || CANVAS_BASE_WIDTH;
    const height = canvasRef.current?.clientHeight || CANVAS_BASE_HEIGHT;
    setCanvasState((state) => ({
      ...state,
      viewport: {
        ...state.viewport,
        x: Math.round(width / 2 - point.x * state.viewport.zoom),
        y: Math.round(height / 2 - point.y * state.viewport.zoom),
      },
    }));
    canvasRef.current?.focus({ preventScroll: true });
  };

  const handleAddNote = (targetPosition?: { x: number; y: number }) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    setCanvasState((state) => {
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
      return {
        ...state,
        nodes,
        selectedNodeId: nodes[nodes.length - 1]?.id || state.selectedNodeId,
        selectedNodeIds: [nodes[nodes.length - 1]?.id || state.selectedNodeId],
      };
    });
    canvasRef.current?.focus({ preventScroll: true });
  };

  const handleCanvasKeyDown = useProductionCanvasKeyboardCommands({
    handleAddNote,
    handleFit,
    handleFocusSelectedNode,
    handleRemoveNode,
    handleSelectNode,
    handleZoomButton,
    selectedNode,
    setCanvasState,
  });

  const appendNodes = (nodes: ProductionCanvasNode[]) => {
    if (!nodes.length) return;
    setCanvasState((state) => {
      const incomingIds = new Set(nodes.map((node) => node.id));
      const nextState = {
        ...state,
        nodes: [
          ...state.nodes.filter((node) => !incomingIds.has(node.id)),
          ...nodes,
        ],
        selectedNodeId: nodes[0]?.id || state.selectedNodeId,
        selectedNodeIds: [nodes[0]?.id || state.selectedNodeId],
      };
      return {
        ...nextState,
        nodes: applyProductionCanvasContext(nextState.nodes),
      };
    });
  };

  return {
    appendNodes,
    canvasRef,
    canvasState,
    handleAddNote,
    handleAddEdge,
    handleCanvasKeyDown,
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleFocusSelectedNode,
    handleNodePointerDown,
    handleNavigate,
    handleReset,
    handleRemoveEdge,
    handleRemoveNode,
    handleSelectNode,
    handleUpdateNode,
    handleUpdateNodeOutputs,
    handleZoomButton,
    replaceCanvasState: setCanvasState,
    selectedNode,
    selectionActions,
    worldBounds,
    zoomLabel,
  };
}
