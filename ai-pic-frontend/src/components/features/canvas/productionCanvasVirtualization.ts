import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasViewport } from "./productionCanvasState";
import { getNodeHeight } from "./productionCanvasViewModel";

export const PRODUCTION_CANVAS_VIRTUALIZATION_THRESHOLD = 80;
export const PRODUCTION_CANVAS_OVERSCAN_PX = 240;

type CanvasSize = { height: number; width: number };

function intersectsViewport(
  node: ProductionCanvasNode,
  viewport: ProductionCanvasViewport,
  canvasSize: CanvasSize,
  overscanPx: number,
) {
  const zoom = Math.max(0.01, viewport.zoom);
  const overscan = overscanPx / zoom;
  const left = -viewport.x / zoom - overscan;
  const top = -viewport.y / zoom - overscan;
  const right = (canvasSize.width - viewport.x) / zoom + overscan;
  const bottom = (canvasSize.height - viewport.y) / zoom + overscan;
  return (
    node.x + node.width >= left &&
    node.x <= right &&
    node.y + getNodeHeight(node) >= top &&
    node.y <= bottom
  );
}

export function virtualizedProductionCanvasNodes(
  nodes: ProductionCanvasNode[],
  viewport: ProductionCanvasViewport,
  canvasSize: CanvasSize,
  alwaysRenderIds: ReadonlySet<string> = new Set(),
  threshold = PRODUCTION_CANVAS_VIRTUALIZATION_THRESHOLD,
  overscanPx = PRODUCTION_CANVAS_OVERSCAN_PX,
) {
  if (nodes.length <= threshold) return nodes;
  return nodes.filter(
    (node) =>
      alwaysRenderIds.has(node.id) ||
      intersectsViewport(node, viewport, canvasSize, overscanPx),
  );
}
