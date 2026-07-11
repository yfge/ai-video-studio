import { useEffect, useMemo, useRef, useState } from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { updateProductionCanvasNode } from "./productionCanvasGraphState";
import { selectProductionCanvasNode } from "./productionCanvasSelection";
import { createProductionCanvasState } from "./productionCanvasState";
import {
  CANVAS_BASE_HEIGHT,
  CANVAS_BASE_WIDTH,
  centerProductionCanvasOnNode,
  getWorldBounds,
  readStoredCanvasState,
} from "./productionCanvasViewModel";
import { useProductionCanvasDefinitionActions } from "./useProductionCanvasDefinitionActions";
import { useProductionCanvasHistory } from "./useProductionCanvasHistory";
import { useProductionCanvasInteractionControls } from "./useProductionCanvasInteractionControls";
import { useProductionCanvasKeyboardCommands } from "./useProductionCanvasKeyboardCommands";

export function useProductionCanvasController(storageKey?: string | null) {
  const history = useProductionCanvasHistory(createProductionCanvasState);
  const {
    canvasState,
    setCanvasDefinition,
    setCanvasState,
    replaceCanvasState,
  } = history;
  const [storageLoaded, setStorageLoaded] = useState(storageKey === null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const worldBounds = useMemo(
    () => getWorldBounds(canvasState.nodes),
    [canvasState.nodes],
  );
  const selectedNode = canvasState.nodes.find(
    (node) => node.id === canvasState.selectedNodeId,
  );
  const definitionActions = useProductionCanvasDefinitionActions({
    canvasRef,
    setCanvasDefinition,
  });
  const zoomLabel = `${Math.round(canvasState.viewport.zoom * 100)}%`;
  const interaction = useProductionCanvasInteractionControls({
    canvasRef,
    canvasState,
    endHistoryGroup: history.endHistoryGroup,
    setCanvasDefinition,
    setCanvasState,
  });

  useEffect(() => {
    replaceCanvasState(readStoredCanvasState(storageKey));
    setStorageLoaded(true);
  }, [replaceCanvasState, storageKey]);

  useEffect(() => {
    if (!storageKey || !storageLoaded || typeof window === "undefined") return;
    window.localStorage.setItem(storageKey, JSON.stringify(canvasState));
  }, [canvasState, storageKey, storageLoaded]);

  const handleSelectNode = (nodeId: string, additive = false) =>
    setCanvasState((state) =>
      selectProductionCanvasNode(state, nodeId, additive),
    );
  const handleSyncNode = (
    nodeId: string,
    patch: Partial<ProductionCanvasNode>,
  ) =>
    setCanvasState((state) => ({
      ...state,
      nodes: updateProductionCanvasNode(state.nodes, nodeId, patch),
    }));
  const handleReset = () => {
    replaceCanvasState(createProductionCanvasState());
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

  const handleCanvasKeyDown = useProductionCanvasKeyboardCommands({
    handleAddNote: definitionActions.handleAddNote,
    handleFit: interaction.handleFit,
    handleFocusSelectedNode,
    handleRedo: history.redo,
    handleRemoveNode: definitionActions.handleRemoveNode,
    handleSelectNode,
    handleUndo: history.undo,
    handleZoomButton: interaction.handleZoomButton,
    selectedNode,
    setCanvasDefinition,
  });

  return {
    ...definitionActions,
    ...interaction,
    canvasRef,
    canvasState,
    canRedo: history.canRedo,
    canUndo: history.canUndo,
    clearHistory: history.clearHistory,
    handleCanvasKeyDown,
    handleFocusSelectedNode,
    handleNavigate,
    handleRedo: history.redo,
    handleReset,
    handleSelectNode,
    handleSyncNode,
    handleUndo: history.undo,
    replaceCanvasState: setCanvasState,
    selectedNode,
    updateCanvasDefinition: setCanvasDefinition,
    worldBounds,
    zoomLabel,
  };
}
