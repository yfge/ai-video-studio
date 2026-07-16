import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import type { PositionedHierarchyNode } from "./productionCanvasHierarchyModel";

export type HierarchyViewport = { x: number; y: number; zoom: number };

const DEFAULT_VIEWPORT: HierarchyViewport = { x: 24, y: 24, zoom: 1 };

export function hierarchyWorldBounds(nodes: PositionedHierarchyNode[]) {
  const maxX = Math.max(1760, ...nodes.map((node) => node.x + node.width));
  const maxY = Math.max(520, ...nodes.map((node) => node.y + node.height));
  return { width: maxX + 80, height: maxY + 80 };
}

function clampZoom(value: number) {
  return Math.min(1.5, Math.max(0.45, Number(value.toFixed(2))));
}

export function useProductionCanvasHierarchyViewport(
  nodes: PositionedHierarchyNode[],
) {
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    origin: HierarchyViewport;
  } | null>(null);
  const [viewport, setViewport] = useState(DEFAULT_VIEWPORT);

  const zoomAt = useCallback(
    (steps: number, anchor?: { x: number; y: number }) => {
      setViewport((current) => {
        const zoom = clampZoom(current.zoom + steps * 0.1);
        if (!anchor || zoom === current.zoom) return { ...current, zoom };
        const worldX = (anchor.x - current.x) / current.zoom;
        const worldY = (anchor.y - current.y) / current.zoom;
        return {
          x: Math.round(anchor.x - worldX * zoom),
          y: Math.round(anchor.y - worldY * zoom),
          zoom,
        };
      });
      canvasRef.current?.focus({ preventScroll: true });
    },
    [],
  );

  const fit = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const bounds = hierarchyWorldBounds(nodes);
    const zoom = clampZoom(
      Math.min(
        1,
        (canvas.clientWidth - 48) / bounds.width,
        520 / bounds.height,
      ),
    );
    setViewport({ x: 24, y: 24, zoom });
    canvas.focus({ preventScroll: true });
  }, [nodes]);

  const focusNode = useCallback(
    (nodeId: string) => {
      const canvas = canvasRef.current;
      const node = nodes.find((item) => item.id === nodeId);
      if (!canvas || !node) return;
      setViewport((current) => ({
        ...current,
        x: Math.round(
          canvas.clientWidth / 2 - (node.x + node.width / 2) * current.zoom,
        ),
        y: Math.round(
          canvas.clientHeight / 2 - (node.y + node.height / 2) * current.zoom,
        ),
      }));
      canvas.focus({ preventScroll: true });
    },
    [nodes],
  );

  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 && event.button !== 1) return;
    const target = event.target;
    if (
      target instanceof Element &&
      target.closest("[data-hierarchy-node],button,a")
    ) {
      return;
    }
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      origin: viewport,
    };
  };

  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    event.preventDefault();
    setViewport({
      ...drag.origin,
      x: Math.round(drag.origin.x + event.clientX - drag.startX),
      y: Math.round(drag.origin.y + event.clientY - drag.startY),
    });
  };

  const onPointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      if (event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
        setViewport((current) => ({
          ...current,
          x: Math.round(
            current.x - (event.shiftKey ? event.deltaY : event.deltaX),
          ),
          y: Math.round(current.y - (event.shiftKey ? 0 : event.deltaY)),
        }));
        return;
      }
      const rect = canvas.getBoundingClientRect();
      zoomAt(event.deltaY < 0 ? 1 : -1, {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      });
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, [zoomAt]);

  return {
    canvasRef,
    fit,
    focusNode,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    viewport,
    zoomAt,
  };
}
