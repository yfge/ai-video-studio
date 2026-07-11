import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasViewport } from "./productionCanvasState";
import { getNodeHeight } from "./productionCanvasViewModel";

export const MINIMAP_WIDTH = 176;
export const MINIMAP_HEIGHT = 104;
const MINIMAP_PADDING = 8;

export type ProductionCanvasWorldBounds = {
  minX: number;
  minY: number;
  width: number;
  height: number;
};

export function productionCanvasMinimapLayout(
  bounds: ProductionCanvasWorldBounds,
) {
  const scale = Math.min(
    (MINIMAP_WIDTH - MINIMAP_PADDING * 2) / bounds.width,
    (MINIMAP_HEIGHT - MINIMAP_PADDING * 2) / bounds.height,
  );
  return {
    scale,
    offsetX: (MINIMAP_WIDTH - bounds.width * scale) / 2,
    offsetY: (MINIMAP_HEIGHT - bounds.height * scale) / 2,
  };
}

export function productionCanvasMinimapNodeRect(
  node: ProductionCanvasNode,
  bounds: ProductionCanvasWorldBounds,
) {
  const layout = productionCanvasMinimapLayout(bounds);
  return {
    left: layout.offsetX + (node.x - bounds.minX) * layout.scale,
    top: layout.offsetY + (node.y - bounds.minY) * layout.scale,
    width: Math.max(4, node.width * layout.scale),
    height: Math.max(3, getNodeHeight(node) * layout.scale),
  };
}

export function productionCanvasMinimapViewportRect(
  viewport: ProductionCanvasViewport,
  bounds: ProductionCanvasWorldBounds,
  canvasSize: { width: number; height: number },
) {
  const layout = productionCanvasMinimapLayout(bounds);
  const zoom = viewport.zoom || 1;
  const left =
    layout.offsetX + (-viewport.x / zoom - bounds.minX) * layout.scale;
  const top =
    layout.offsetY + (-viewport.y / zoom - bounds.minY) * layout.scale;
  return {
    left,
    top,
    width: (canvasSize.width / zoom) * layout.scale,
    height: (canvasSize.height / zoom) * layout.scale,
  };
}

export function productionCanvasWorldPointFromMinimap(
  point: { x: number; y: number },
  bounds: ProductionCanvasWorldBounds,
) {
  const layout = productionCanvasMinimapLayout(bounds);
  const clamp = (value: number, min: number, max: number) =>
    Math.min(max, Math.max(min, value));
  return {
    x: clamp(
      (point.x - layout.offsetX) / layout.scale + bounds.minX,
      bounds.minX,
      bounds.minX + bounds.width,
    ),
    y: clamp(
      (point.y - layout.offsetY) / layout.scale + bounds.minY,
      bounds.minY,
      bounds.minY + bounds.height,
    ),
  };
}
