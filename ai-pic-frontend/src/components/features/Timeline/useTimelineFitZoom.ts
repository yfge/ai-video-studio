"use client";

import { useEffect, useRef, useState } from "react";
import { BASE_PX_PER_MS, clamp } from "./timelineScale";

const MIN_ZOOM = 0.05;
const MIN_READABLE_FIT_ZOOM = 0.18;
const MAX_ZOOM = 4;

type TimelineFitMode = "full-episode" | "manual" | "readable-window";

export function useTimelineFitZoom({
  fitToWidth,
  initialZoom,
  totalMs,
  trackLabelWidth,
  trackRightPadding,
}: {
  fitToWidth: boolean;
  initialZoom: number;
  totalMs: number;
  trackLabelWidth: number;
  trackRightPadding: number;
}) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const [zoom, setZoom] = useState(clamp(initialZoom, MIN_ZOOM, MAX_ZOOM));
  const [viewportWidth, setViewportWidth] = useState(0);
  const [userAdjustedZoom, setUserAdjustedZoom] = useState(false);
  const measuredWidth = viewportWidth || 600;
  const rawFitZoom =
    (measuredWidth - trackLabelWidth - trackRightPadding) /
    (totalMs * BASE_PX_PER_MS);
  const fitMode: TimelineFitMode =
    fitToWidth && rawFitZoom < MIN_READABLE_FIT_ZOOM
      ? "readable-window"
      : fitToWidth
      ? "full-episode"
      : "manual";
  const fitZoom = clamp(
    rawFitZoom,
    fitToWidth ? MIN_READABLE_FIT_ZOOM : MIN_ZOOM,
    MAX_ZOOM,
  );

  useEffect(() => {
    const node = viewportRef.current;
    if (!node) return;
    const updateWidth = () => setViewportWidth(node.clientWidth);
    updateWidth();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(updateWidth);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!fitToWidth || userAdjustedZoom) return;
    setZoom(fitZoom);
  }, [fitToWidth, fitZoom, userAdjustedZoom, viewportWidth]);

  const setManualZoom = (value: number) => {
    setUserAdjustedZoom(true);
    setZoom(clamp(value, MIN_ZOOM, MAX_ZOOM));
  };

  const resetZoom = () => {
    if (fitToWidth) {
      setUserAdjustedZoom(false);
      setZoom(fitZoom);
      return;
    }
    setManualZoom(1);
  };

  return {
    fitZoom,
    fitMode,
    maxZoom: MAX_ZOOM,
    measuredWidth,
    minZoom: MIN_ZOOM,
    resetZoom,
    setManualZoom,
    viewportRef,
    zoom,
  };
}
