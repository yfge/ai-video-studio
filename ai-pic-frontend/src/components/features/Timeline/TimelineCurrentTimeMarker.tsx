"use client";

import { formatTimelineLabel } from "./timelineScale";

export function TimelineCurrentTimeMarker({
  currentTimeMs,
  minStart,
  pxPerMs,
  trackLabelWidth,
}: {
  currentTimeMs: number;
  minStart: number;
  pxPerMs: number;
  trackLabelWidth: number;
}) {
  return (
    <div
      className="pointer-events-none absolute top-0 bottom-0 border-l-2 border-blue-500/70"
      style={{ left: trackLabelWidth + (currentTimeMs - minStart) * pxPerMs }}
    >
      <div className="absolute -top-5 -translate-x-1/2 rounded bg-blue-500 px-1 py-0.5 text-[10px] text-white">
        {formatTimelineLabel(currentTimeMs)}
      </div>
    </div>
  );
}
