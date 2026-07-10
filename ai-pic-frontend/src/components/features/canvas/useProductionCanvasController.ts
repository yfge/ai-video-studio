import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  addProductionCanvasEdge,
  removeProductionCanvasEdge,
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
import {
  applyProductionCanvasKeyboardNudge,
  getProductionCanvasKeyboardNudge,
} from "./productionCanvasKeyboard";

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
  const zoomLabel = `${Math.round(canvasState.viewport.zoom * 100)}%`;
  const {
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleNodePointerDown,
    handleWheel,
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

  const handleSelectNode = (nodeId: string) =>
    setCanvasState((state) => ({ ...state, selectedNodeId: nodeId }));

  const handleFocusSelectedNode = (nodeId?: string) => {
    const width = canvasRef.current?.clientWidth || CANVAS_BASE_WIDTH;
    const height = canvasRef.current?.clientHeight || CANVAS_BASE_HEIGHT;
    setCanvasState((state) => {
      const targetNodeId = nodeId || state.selectedNodeId;
      const node = state.nodes.find((item) => item.id === targetNodeId);
      if (!node) return state;
      return {
        ...state,
        selectedNodeId: node.id,
        viewport: centerProductionCanvasOnNode(state.viewport, node, {
          width,
          height,
        }),
      };
    });
    canvasRef.current?.focus({ preventScroll: true });
  };

  const handleCanvasKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      handleSelectNode("");
      return;
    }
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key.toLowerCase() === "f" && selectedNode) {
      event.preventDefault();
      handleFocusSelectedNode();
      return;
    }
    if (event.key === "+" || event.key === "=" || event.key === "-") {
      event.preventDefault();
      handleZoomButton(event.key === "-" ? -1 : 1);
      return;
    }
    if (event.key === "0" || event.key === "Home") {
      event.preventDefault();
      handleFit();
      return;
    }
    const nudge = getProductionCanvasKeyboardNudge(event.key, event.shiftKey);
    if (!nudge) return;
    event.preventDefault();
    setCanvasState((state) => applyProductionCanvasKeyboardNudge(state, nudge));
  };

  const handleAddEdge = (from: string, to: string) =>
    setCanvasState((state) => ({
      ...state,
      edges: addProductionCanvasEdge(state.edges, from, to),
    }));
  const handleRemoveEdge = (from: string, to: string) =>
    setCanvasState((state) => ({
      ...state,
      edges: removeProductionCanvasEdge(state.edges, from, to),
    }));

  const handleUpdateNodeOutputs = (
    nodeId: string,
    patch: ProductionCanvasOutputPatch,
  ) =>
    setCanvasState((state) => ({
      ...state,
      nodes: updateProductionCanvasNodeOutputs(state.nodes, nodeId, patch),
    }));

  const handleReset = () => {
    setCanvasState(createProductionCanvasState());
    if (storageKey && typeof window !== "undefined") {
      window.localStorage.removeItem(storageKey);
    }
  };

  const handleAddNote = () => {
    const rect = canvasRef.current?.getBoundingClientRect();
    setCanvasState((state) => {
      const position = {
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
      };
    });
  };

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
    handleReset,
    handleRemoveEdge,
    handleSelectNode,
    handleUpdateNodeOutputs,
    handleWheel,
    handleZoomButton,
    replaceCanvasState: setCanvasState,
    selectedNode,
    worldBounds,
    zoomLabel,
  };
}
