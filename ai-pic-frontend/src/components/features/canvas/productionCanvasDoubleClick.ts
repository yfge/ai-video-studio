import type { MouseEvent as ReactMouseEvent } from "react";

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
  if (!nodeElement || !event.currentTarget.contains(nodeElement)) return null;
  return nodeElement.getAttribute("data-canvas-node");
}
