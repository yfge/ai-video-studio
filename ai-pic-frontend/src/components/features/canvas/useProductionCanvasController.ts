import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  addProductionCanvasNote,
  createProductionCanvasState,
  moveProductionCanvasNode,
  panProductionCanvas,
  zoomProductionCanvas,
  type ProductionCanvasViewport,
} from "./productionCanvasState";
import {
  CANVAS_BASE_HEIGHT,
  CANVAS_BASE_WIDTH,
  getWorldBounds,
  readStoredCanvasState,
} from "./productionCanvasViewModel";

type CanvasDragState =
  | {
      type: "node";
      nodeId: string;
      startX: number;
      startY: number;
      originNodes: ProductionCanvasNode[];
      zoom: number;
    }
  | {
      type: "pan";
      startX: number;
      startY: number;
      originViewport: ProductionCanvasViewport;
    };

export function useProductionCanvasController(storageKey?: string | null) {
  const [canvasState, setCanvasState] = useState(createProductionCanvasState);
  const [storageLoaded, setStorageLoaded] = useState(storageKey === null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<CanvasDragState | null>(null);
  const worldBounds = useMemo(
    () => getWorldBounds(canvasState.nodes),
    [canvasState.nodes],
  );
  const selectedNode =
    canvasState.nodes.find((node) => node.id === canvasState.selectedNodeId) ||
    canvasState.nodes[0];
  const zoomLabel = `${Math.round(canvasState.viewport.zoom * 100)}%`;

  useEffect(() => {
    setCanvasState(readStoredCanvasState(storageKey));
    setStorageLoaded(true);
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey || !storageLoaded || typeof window === "undefined") return;
    window.localStorage.setItem(storageKey, JSON.stringify(canvasState));
  }, [canvasState, storageKey, storageLoaded]);

  const capturePointer = (pointerId: number) => {
    canvasRef.current?.setPointerCapture(pointerId);
  };

  const releasePointer = (pointerId: number) => {
    if (!canvasRef.current?.hasPointerCapture(pointerId)) return;
    canvasRef.current.releasePointerCapture(pointerId);
  };

  const handleNodePointerDown = (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => {
    if (event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    capturePointer(event.pointerId);
    setCanvasState((state) => ({ ...state, selectedNodeId: nodeId }));
    dragRef.current = {
      type: "node",
      nodeId,
      startX: event.clientX,
      startY: event.clientY,
      originNodes: canvasState.nodes,
      zoom: canvasState.viewport.zoom,
    };
  };

  const handleCanvasPointerDown = (
    event: ReactPointerEvent<HTMLDivElement>,
  ) => {
    if (event.button !== 0) return;
    const target = event.target;
    if (target instanceof Element && target.closest("[data-canvas-node]")) {
      return;
    }
    event.preventDefault();
    capturePointer(event.pointerId);
    dragRef.current = {
      type: "pan",
      startX: event.clientX,
      startY: event.clientY,
      originViewport: canvasState.viewport,
    };
  };

  const handleCanvasPointerMove = (
    event: ReactPointerEvent<HTMLDivElement>,
  ) => {
    const drag = dragRef.current;
    if (!drag) return;
    event.preventDefault();
    if (drag.type === "node") {
      setCanvasState((state) => ({
        ...state,
        nodes: moveProductionCanvasNode(
          drag.originNodes,
          drag.nodeId,
          (event.clientX - drag.startX) / drag.zoom,
          (event.clientY - drag.startY) / drag.zoom,
        ),
      }));
      return;
    }
    setCanvasState((state) => ({
      ...state,
      viewport: panProductionCanvas(
        drag.originViewport,
        event.clientX - drag.startX,
        event.clientY - drag.startY,
      ),
    }));
  };

  const handleCanvasPointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    dragRef.current = null;
    releasePointer(event.pointerId);
  };

  const handleWheel = (event: ReactWheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    setCanvasState((state) => ({
      ...state,
      viewport: zoomProductionCanvas(state.viewport, event.deltaY < 0 ? 1 : -1, {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      }),
    }));
  };

  const handleSelectNode = (nodeId: string) => {
    setCanvasState((state) => ({ ...state, selectedNodeId: nodeId }));
  };

  const handleZoomButton = (steps: number) => {
    setCanvasState((state) => ({
      ...state,
      viewport: zoomProductionCanvas(state.viewport, steps),
    }));
  };

  const handleFit = () => {
    const width = canvasRef.current?.clientWidth || CANVAS_BASE_WIDTH;
    const height = canvasRef.current?.clientHeight || CANVAS_BASE_HEIGHT;
    const zoom = Math.min(
      1,
      Math.max(
        0.5,
        Number(
          Math.min(
            (width - 48) / CANVAS_BASE_WIDTH,
            (height - 48) / CANVAS_BASE_HEIGHT,
          ).toFixed(2),
        ),
      ),
    );
    setCanvasState((state) => ({ ...state, viewport: { x: 24, y: 24, zoom } }));
  };

  const handleReset = () => {
    setCanvasState(createProductionCanvasState());
    if (storageKey && typeof window !== "undefined") {
      window.localStorage.removeItem(storageKey);
    }
  };

  const handleAddNote = () => {
    const rect = canvasRef.current?.getBoundingClientRect();
    const viewportCenter = { x: (rect?.width || 720) / 2, y: (rect?.height || 420) / 2 };
    setCanvasState((state) => {
      const position = {
        x: (viewportCenter.x - state.viewport.x) / state.viewport.zoom - 95,
        y: (viewportCenter.y - state.viewport.y) / state.viewport.zoom - 48,
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
      return {
        ...state,
        nodes: [
          ...state.nodes.filter((node) => !incomingIds.has(node.id)),
          ...nodes,
        ],
        selectedNodeId: nodes[0]?.id || state.selectedNodeId,
      };
    });
  };

  return {
    appendNodes,
    canvasRef,
    canvasState,
    handleAddNote,
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleNodePointerDown,
    handleReset,
    handleSelectNode,
    handleWheel,
    handleZoomButton,
    selectedNode,
    worldBounds,
    zoomLabel,
  };
}
