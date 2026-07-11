import type {
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
  RefObject,
} from "react";
import { useEffect, useState } from "react";
import { CanvasEdges } from "./ProductionCanvasElements";
import { ProductionCanvasMinimap } from "./ProductionCanvasMinimap";
import {
  ProductionCanvasConnectionOverlay,
  useProductionCanvasPortConnections,
} from "./ProductionCanvasPortConnections";
import { CanvasNodeCard } from "./ProductionCanvasNodeCard";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasState } from "./productionCanvasState";
import { selectedProductionCanvasNodeIds } from "./productionCanvasSelection";
import {
  CANVAS_BASE_HEIGHT,
  CANVAS_BASE_WIDTH,
} from "./productionCanvasViewModel";

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
  onCanvasDoubleClick,
  onCanvasKeyDown,
  onCanvasPointerDown,
  onCanvasPointerMove,
  onCanvasPointerUp,
  onAddEdge,
  onExecuteNode,
  onFocusNode,
  onNavigate,
  onNodePointerDown,
  onSelectNode,
  selectedNodeId,
  visibleNodeIds,
  worldBounds,
}: {
  canvasRef: RefObject<HTMLDivElement | null>;
  canvasState: ProductionCanvasState;
  executingNodeId?: string | null;
  onCanvasDoubleClick: (event: ReactMouseEvent<HTMLDivElement>) => void;
  onCanvasKeyDown: (event: ReactKeyboardEvent<HTMLDivElement>) => void;
  onCanvasPointerDown: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onCanvasPointerMove: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onCanvasPointerUp: (event: ReactPointerEvent<HTMLDivElement>) => void;
  onAddEdge: (edge: ProductionCanvasState["edges"][number]) => void;
  onExecuteNode: (node: ProductionCanvasNode) => void;
  onFocusNode: (nodeId?: string) => void;
  onNavigate: (point: { x: number; y: number }) => void;
  onNodePointerDown: (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => void;
  onSelectNode: (nodeId: string, additive?: boolean) => void;
  selectedNodeId?: string;
  visibleNodeIds?: Set<string>;
  worldBounds: WorldBounds;
}) {
  const [canvasSize, setCanvasSize] = useState({
    width: CANVAS_BASE_WIDTH,
    height: CANVAS_BASE_HEIGHT,
  });
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      if (!entry) return;
      setCanvasSize({
        width: entry.contentRect.width || CANVAS_BASE_WIDTH,
        height: entry.contentRect.height || CANVAS_BASE_HEIGHT,
      });
    });
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [canvasRef]);
  const visibleNodes = visibleNodeIds
    ? canvasState.nodes.filter((node) => visibleNodeIds.has(node.id))
    : canvasState.nodes;
  const visibleEdges = visibleNodeIds
    ? canvasState.edges.filter(
        (edge) => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to),
      )
    : canvasState.edges;
  const selectedNodeIds = new Set(selectedProductionCanvasNodeIds(canvasState));
  const connections = useProductionCanvasPortConnections({
    canvasRef,
    edges: canvasState.edges,
    nodes: canvasState.nodes,
    onAddEdge,
    onFocusNode,
  });
  return (
    <div
      ref={canvasRef}
      aria-label="短剧生产链路无限画布"
      className="relative h-[560px] overflow-hidden touch-none bg-[#f8fafc]"
      data-production-canvas="infinite-canvas"
      role="region"
      tabIndex={0}
      onKeyDown={onCanvasKeyDown}
      onPointerDown={onCanvasPointerDown}
      onPointerMove={(event) => {
        connections.move(event);
        onCanvasPointerMove(event);
      }}
      onPointerUp={(event) => {
        connections.finish(event);
        onCanvasPointerUp(event);
      }}
      onPointerCancel={(event) => {
        connections.cancel();
        onCanvasPointerUp(event);
      }}
      onDoubleClick={onCanvasDoubleClick}
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
          edges={visibleEdges}
          nodes={visibleNodes}
          worldBounds={worldBounds}
        />
        {visibleNodes.map((node) => (
          <CanvasNodeCard
            key={node.id}
            executionDisabled={Boolean(
              executingNodeId && executingNodeId !== node.id,
            )}
            executing={executingNodeId === node.id}
            node={node}
            selected={selectedNodeIds.has(node.id)}
            worldBounds={worldBounds}
            onExecuteNode={onExecuteNode}
            onFocusNode={onFocusNode}
            onOutputPortPointerDown={connections.start}
            onSelect={onSelectNode}
            onPointerDown={onNodePointerDown}
          />
        ))}
      </div>
      {!visibleNodes.length ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-gray-500">
          无匹配节点
        </div>
      ) : null}
      <ProductionCanvasMinimap
        bounds={worldBounds}
        canvasSize={canvasSize}
        nodes={visibleNodes}
        selectedNodeId={selectedNodeId}
        viewport={canvasState.viewport}
        onFocusNode={onFocusNode}
        onNavigate={onNavigate}
      />
      <ProductionCanvasConnectionOverlay
        discovery={connections.discovery}
        draft={connections.draft}
        nodes={visibleNodes}
        onCancel={connections.cancel}
        onChoose={connections.choose}
      />
    </div>
  );
}
