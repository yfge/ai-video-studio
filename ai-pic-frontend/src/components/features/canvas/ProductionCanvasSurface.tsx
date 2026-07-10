import type {
  PointerEvent as ReactPointerEvent,
  RefObject,
  WheelEvent as ReactWheelEvent,
} from "react";
import { CanvasEdges } from "./ProductionCanvasElements";
import { CanvasNodeCard } from "./ProductionCanvasNodeCard";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasState } from "./productionCanvasState";

type WorldBounds = {
  minX: number;
  minY: number;
  width: number;
  height: number;
};

export function ProductionCanvasSurface({
  canvasRef,
  canvasState,
  executingNodeId,
  onCanvasPointerDown,
  onCanvasPointerMove,
  onCanvasPointerUp,
  onCanvasWheel,
  onExecuteNode,
  onNodePointerDown,
  onSelectNode,
  selectedNodeId,
  worldBounds,
}: {
  canvasRef: RefObject<HTMLDivElement | null>;
  canvasState: ProductionCanvasState;
  executingNodeId?: string | null;
  onCanvasPointerDown: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onCanvasPointerMove: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onCanvasPointerUp: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onCanvasWheel: (event: ReactWheelEvent<HTMLDivElement>) => void;
  onExecuteNode: (node: ProductionCanvasNode) => void;
  onNodePointerDown: (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => void;
  onSelectNode: (nodeId: string) => void;
  selectedNodeId?: string;
  worldBounds: WorldBounds;
}) {
  return (
    <div
      ref={canvasRef}
      className="relative h-[560px] overflow-hidden touch-none bg-[#f8fafc]"
      data-production-canvas="infinite-canvas"
      tabIndex={-1}
      onPointerDown={onCanvasPointerDown}
      onPointerMove={onCanvasPointerMove}
      onPointerUp={onCanvasPointerUp}
      onPointerCancel={onCanvasPointerUp}
      onWheel={onCanvasWheel}
    >
      <div
        className="absolute left-0 top-0"
        data-production-canvas-world="true"
        style={{
          width: worldBounds.width,
          height: worldBounds.height,
          transform: `translate(${canvasState.viewport.x}px, ${canvasState.viewport.y}px) scale(${canvasState.viewport.zoom}) translate(${worldBounds.minX}px, ${worldBounds.minY}px)`,
          transformOrigin: "0 0",
        }}
      >
        <div className="absolute inset-0 bg-[linear-gradient(#e5e7eb_1px,transparent_1px),linear-gradient(90deg,#e5e7eb_1px,transparent_1px)] bg-[size:32px_32px]" />
        <CanvasEdges
          edges={canvasState.edges}
          nodes={canvasState.nodes}
          worldBounds={worldBounds}
        />
        {canvasState.nodes.map((node) => (
          <CanvasNodeCard
            key={node.id}
            executing={executingNodeId === node.id}
            node={node}
            selected={node.id === selectedNodeId}
            worldBounds={worldBounds}
            onExecuteNode={onExecuteNode}
            onSelect={onSelectNode}
            onPointerDown={onNodePointerDown}
          />
        ))}
      </div>
    </div>
  );
}
