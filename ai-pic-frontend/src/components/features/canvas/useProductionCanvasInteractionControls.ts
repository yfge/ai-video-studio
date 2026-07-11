import {
  useEffect,
  useRef,
  type Dispatch,
  type RefObject,
  type SetStateAction,
  type PointerEvent as ReactPointerEvent,
} from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  moveProductionCanvasNodes,
  selectedProductionCanvasNodeIds,
  selectProductionCanvasNode,
} from "./productionCanvasSelection";
import {
  panProductionCanvas,
  zoomProductionCanvas,
  type ProductionCanvasState,
  type ProductionCanvasViewport,
} from "./productionCanvasState";
import {
  CANVAS_BASE_HEIGHT,
  CANVAS_BASE_WIDTH,
  getWorldBounds,
} from "./productionCanvasViewModel";
import type { ProductionCanvasDefinitionSetter } from "./useProductionCanvasHistory";

type CanvasDragState =
  | {
      type: "node";
      historyGroup: string;
      nodeIds: string[];
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

type UseProductionCanvasInteractionControlsArgs = {
  canvasRef: RefObject<HTMLDivElement | null>;
  canvasState: ProductionCanvasState;
  endHistoryGroup: () => void;
  setCanvasDefinition: ProductionCanvasDefinitionSetter;
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
};

export function useProductionCanvasInteractionControls({
  canvasRef,
  canvasState,
  endHistoryGroup,
  setCanvasDefinition,
  setCanvasState,
}: UseProductionCanvasInteractionControlsArgs) {
  const dragRef = useRef<CanvasDragState | null>(null);

  const handleNodePointerDown = (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => {
    if (event.button !== 0 || event.altKey) return;
    event.preventDefault();
    event.stopPropagation();
    canvasRef.current?.setPointerCapture(event.pointerId);
    canvasRef.current?.focus({ preventScroll: true });
    const selected = selectedProductionCanvasNodeIds(canvasState);
    const additive = event.shiftKey || event.metaKey || event.ctrlKey;
    if (additive && selected.includes(nodeId)) {
      setCanvasState((state) =>
        selectProductionCanvasNode(state, nodeId, true),
      );
      return;
    }
    const nodeIds = additive
      ? [...selected, nodeId]
      : selected.includes(nodeId) && selected.length > 1
      ? selected
      : [nodeId];
    setCanvasState((state) => ({
      ...state,
      selectedNodeId: nodeId,
      selectedNodeIds: nodeIds,
    }));
    dragRef.current = {
      type: "node",
      historyGroup: `node-drag-${event.pointerId}-${event.clientX}-${event.clientY}`,
      nodeIds,
      startX: event.clientX,
      startY: event.clientY,
      originNodes: canvasState.nodes,
      zoom: canvasState.viewport.zoom,
    };
  };

  const handleCanvasPointerDown = (
    event: ReactPointerEvent<HTMLDivElement>,
  ) => {
    if (event.button !== 0 && event.button !== 1) return;
    const target = event.target;
    if (
      event.button === 0 &&
      !event.altKey &&
      target instanceof Element &&
      target.closest("[data-canvas-node]")
    ) {
      return;
    }
    event.preventDefault();
    canvasRef.current?.setPointerCapture(event.pointerId);
    canvasRef.current?.focus({ preventScroll: true });
    if (event.button === 0 && !event.altKey) {
      setCanvasState((state) => ({
        ...state,
        selectedNodeId: "",
        selectedNodeIds: [],
      }));
    }
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
      setCanvasDefinition(
        (state) => ({
          ...state,
          nodes: moveProductionCanvasNodes(
            drag.originNodes,
            drag.nodeIds,
            (event.clientX - drag.startX) / drag.zoom,
            (event.clientY - drag.startY) / drag.zoom,
          ),
        }),
        drag.historyGroup,
      );
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
    if (dragRef.current?.type === "node") endHistoryGroup();
    dragRef.current = null;
    if (canvasRef.current?.hasPointerCapture(event.pointerId)) {
      canvasRef.current.releasePointerCapture(event.pointerId);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const handleWheel = (event: WheelEvent) => {
      event.preventDefault();
      canvas.focus({ preventScroll: true });
      if (event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
        setCanvasState((state) => ({
          ...state,
          viewport: panProductionCanvas(
            state.viewport,
            event.shiftKey ? -event.deltaY : -event.deltaX,
            event.shiftKey ? 0 : -event.deltaY,
          ),
        }));
        return;
      }
      const rect = canvas.getBoundingClientRect();
      setCanvasState((state) => ({
        ...state,
        viewport: zoomProductionCanvas(
          state.viewport,
          event.deltaY < 0 ? 1 : -1,
          {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          },
        ),
      }));
    };
    canvas.addEventListener("wheel", handleWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", handleWheel);
  }, [canvasRef, setCanvasState]);

  const handleZoomButton = (steps: number) => {
    setCanvasState((state) => ({
      ...state,
      viewport: zoomProductionCanvas(state.viewport, steps),
    }));
    canvasRef.current?.focus({ preventScroll: true });
  };

  const handleFit = () => {
    const width = canvasRef.current?.clientWidth || CANVAS_BASE_WIDTH;
    const height = canvasRef.current?.clientHeight || CANVAS_BASE_HEIGHT;
    setCanvasState((state) => {
      const bounds = getWorldBounds(state.nodes);
      const zoom = Math.min(
        1,
        Math.max(
          0.5,
          Number(
            Math.min(
              (width - 48) / bounds.width,
              (height - 48) / bounds.height,
            ).toFixed(2),
          ),
        ),
      );
      return {
        ...state,
        viewport: {
          x: Math.round(24 - bounds.minX * zoom),
          y: Math.round(24 - bounds.minY * zoom),
          zoom,
        },
      };
    });
  };

  return {
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleNodePointerDown,
    handleZoomButton,
  };
}
