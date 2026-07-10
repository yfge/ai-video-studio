import {
  useRef,
  type Dispatch,
  type RefObject,
  type SetStateAction,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  moveProductionCanvasNode,
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

type UseProductionCanvasInteractionControlsArgs = {
  canvasRef: RefObject<HTMLDivElement | null>;
  canvasState: ProductionCanvasState;
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
};

export function useProductionCanvasInteractionControls({
  canvasRef,
  canvasState,
  setCanvasState,
}: UseProductionCanvasInteractionControlsArgs) {
  const dragRef = useRef<CanvasDragState | null>(null);

  const handleNodePointerDown = (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => {
    if (event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    canvasRef.current?.setPointerCapture(event.pointerId);
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
    canvasRef.current?.setPointerCapture(event.pointerId);
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
    if (canvasRef.current?.hasPointerCapture(event.pointerId)) {
      canvasRef.current.releasePointerCapture(event.pointerId);
    }
  };

  const handleWheel = (event: ReactWheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
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

  const handleZoomButton = (steps: number) =>
    setCanvasState((state) => ({
      ...state,
      viewport: zoomProductionCanvas(state.viewport, steps),
    }));

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
    handleWheel,
    handleZoomButton,
  };
}
