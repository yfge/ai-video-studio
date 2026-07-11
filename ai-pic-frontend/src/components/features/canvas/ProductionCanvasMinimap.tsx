import type { MouseEvent as ReactMouseEvent } from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasViewport } from "./productionCanvasState";
import {
  MINIMAP_HEIGHT,
  MINIMAP_WIDTH,
  productionCanvasMinimapNodeRect,
  productionCanvasMinimapViewportRect,
  productionCanvasWorldPointFromMinimap,
  type ProductionCanvasWorldBounds,
} from "./productionCanvasMinimapModel";

export function ProductionCanvasMinimap({
  bounds,
  canvasSize,
  nodes,
  onFocusNode,
  onNavigate,
  selectedNodeId,
  viewport,
}: {
  bounds: ProductionCanvasWorldBounds;
  canvasSize: { width: number; height: number };
  nodes: ProductionCanvasNode[];
  onFocusNode: (nodeId?: string) => void;
  onNavigate: (point: { x: number; y: number }) => void;
  selectedNodeId?: string;
  viewport: ProductionCanvasViewport;
}) {
  const viewportRect = productionCanvasMinimapViewportRect(
    viewport,
    bounds,
    canvasSize,
  );
  const navigate = (event: ReactMouseEvent<HTMLButtonElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    onNavigate(
      productionCanvasWorldPointFromMinimap(
        {
          x: ((event.clientX - rect.left) / rect.width) * MINIMAP_WIDTH,
          y: ((event.clientY - rect.top) / rect.height) * MINIMAP_HEIGHT,
        },
        bounds,
      ),
    );
  };

  return (
    <nav
      aria-label="画布小地图"
      className="absolute bottom-3 right-3 z-20 overflow-hidden rounded-md border border-gray-300 bg-white/95 shadow-sm"
      style={{ width: MINIMAP_WIDTH, height: MINIMAP_HEIGHT }}
      onPointerDown={(event) => event.stopPropagation()}
    >
      <button
        type="button"
        aria-label="移动画布视口"
        className="absolute inset-0 h-full w-full bg-[linear-gradient(#e5e7eb_1px,transparent_1px),linear-gradient(90deg,#e5e7eb_1px,transparent_1px)] bg-[size:16px_16px]"
        onClick={navigate}
      />
      {nodes.map((node) => {
        const nodeRect = productionCanvasMinimapNodeRect(node, bounds);
        const selected = node.id === selectedNodeId;
        return (
          <button
            key={node.id}
            type="button"
            aria-label={`小地图定位 ${node.label}`}
            aria-pressed={selected}
            className={`absolute min-h-[3px] min-w-1 border ${
              selected
                ? "z-20 border-blue-700 bg-blue-500"
                : "z-10 border-gray-500 bg-gray-400 hover:bg-blue-400"
            }`}
            style={nodeRect}
            title={node.label}
            onClick={(event) => {
              event.stopPropagation();
              onFocusNode(node.id);
            }}
          />
        );
      })}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute z-30 border-2 border-blue-600 bg-blue-100/20"
        style={viewportRect}
      />
    </nav>
  );
}
