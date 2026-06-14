"use client";

import { useEffect, useRef } from "react";

export function useTimelineSelectionVisibility(selectedItemId: string | null) {
  const timelineCanvasRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!selectedItemId) return;
    const timelineCanvas = timelineCanvasRef.current;
    if (!timelineCanvas || typeof window === "undefined") return;
    if (typeof timelineCanvas.scrollIntoView !== "function") return;

    const rect = timelineCanvas.getBoundingClientRect();
    const viewportHeight =
      window.innerHeight || document.documentElement.clientHeight || 0;
    const visibleHeight = Math.max(
      0,
      Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0),
    );
    const requiredVisibleHeight = Math.min(220, rect.height * 0.7);
    const aboveViewport = rect.bottom < 96;
    const belowViewport = viewportHeight > 0 && rect.top > viewportHeight - 120;
    const mostlyHidden =
      viewportHeight > 0 && visibleHeight < requiredVisibleHeight;
    if (!aboveViewport && !belowViewport && !mostlyHidden) return;

    timelineCanvas.scrollIntoView({ block: "start", behavior: "smooth" });
  }, [selectedItemId]);

  return timelineCanvasRef;
}
