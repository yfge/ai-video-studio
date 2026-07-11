import type { MouseEvent as ReactMouseEvent } from "react";
import type { ProductionCanvasViewport } from "./productionCanvasState";

const safeZoom = (zoom: number) => {
  const value = Number(zoom);
  return Math.min(1.6, Math.max(0.5, Number.isFinite(value) ? value : 1));
};

export function nodeIdFromCanvasDoubleClick(
  event: ReactMouseEvent<HTMLDivElement>,
) {
  const target = event.target as HTMLElement | null;
  const path = event.nativeEvent.composedPath?.() || [];
  const pathNode = path.find(
    (item) => (item as HTMLElement).hasAttribute?.("data-canvas-node"),
  ) as HTMLElement | undefined;
  const hitNode = event.currentTarget.ownerDocument
    .elementFromPoint?.(event.clientX, event.clientY)
    ?.closest?.("[data-canvas-node]");
  const nodeElement =
    target?.closest?.("[data-canvas-node]") || pathNode || hitNode;
  if (!nodeElement || !event.currentTarget.contains(nodeElement)) {
    return null;
  }
  return nodeElement.getAttribute("data-canvas-node");
}

export function notePositionFromCanvasDoubleClick(
  event: ReactMouseEvent<HTMLDivElement>,
  viewport: ProductionCanvasViewport,
) {
  const rect = event.currentTarget.getBoundingClientRect();
  const zoom = safeZoom(viewport.zoom);
  return {
    x: (event.clientX - rect.left - viewport.x) / zoom - 95,
    y: (event.clientY - rect.top - viewport.y) / zoom - 48,
  };
}
