"use client";

import { formatTimelineLabel } from "./timelineScale";
import type { TimelineItem, TimelineTrack } from "./TimelineTypes";

export function findSelectedTimelineItem(
  tracks: TimelineTrack[],
  selectedItemId?: string | null,
) {
  if (!selectedItemId) return null;
  for (const [trackIndex, track] of tracks.entries()) {
    const item = track.items.find(
      (candidate) => candidate.id === selectedItemId,
    );
    if (item) return { item, trackIndex };
  }
  return null;
}

export function TimelineSelectedMarker({
  contentWidth,
  item,
  minStart,
  pxPerMs,
  tickLaneHeight,
  trackLabelWidth,
}: {
  contentWidth: number;
  item: TimelineItem;
  minStart: number;
  pxPerMs: number;
  tickLaneHeight: number;
  trackLabelWidth: number;
}) {
  const startOffset = (item.startMs - minStart) * pxPerMs;
  const width = Math.max(Math.max(item.endMs - item.startMs, 0) * pxPerMs, 14);
  const left = Math.min(
    Math.max(trackLabelWidth + startOffset, trackLabelWidth),
    Math.max(trackLabelWidth, contentWidth - width),
  );
  const label = `${shortTimelineMs(item.startMs)}-${shortTimelineMs(
    item.endMs,
  )}`;

  return (
    <>
      <span className="sr-only">当前片段 · {label}</span>
      <div
        data-timeline-selected-range="true"
        className="pointer-events-none absolute bottom-2 z-10 rounded-sm border-x border-blue-400/35 bg-blue-50/25"
        style={{ left, top: tickLaneHeight, width }}
      />
      <div
        data-timeline-selected-cursor="true"
        className="pointer-events-none absolute bottom-2 z-30 w-px bg-blue-500/45"
        style={{ left, top: tickLaneHeight }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute z-30 h-1.5 w-1.5 -translate-x-1/2 rotate-45 rounded-[1px] bg-blue-500/70"
        style={{ left, top: tickLaneHeight }}
      />
    </>
  );
}

function shortTimelineMs(ms: number) {
  return formatTimelineLabel(ms);
}
