"use client";

import { formatTimelineLabel } from "./timelineScale";
import type { TimelineItem, TimelineTrack } from "./TimelineTypes";

export function TimelineSelectedContext({
  item,
  track,
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
}) {
  if (!item) return null;

  const label = item.displayLabel || item.label || "片段";
  const trackLabel = track?.label ? `${track.label}轨` : "当前片段";
  const preciseRange = `${formatTimelineLabel(
    item.startMs,
  )}-${formatTimelineLabel(item.endMs)}`;
  const compactRange = `${formatCompactTimelineLabel(
    item.startMs,
  )}-${formatCompactTimelineLabel(item.endMs)}`;

  return (
    <div
      data-timeline-selected-context="true"
      data-timeline-selected-context-style="inline"
      className="flex min-w-0 items-center gap-1 text-[11px] leading-4 text-slate-500 max-[560px]:sr-only"
      title={`${trackLabel} · ${label} · ${preciseRange}`}
    >
      <span className="shrink-0 font-medium text-slate-600">当前</span>
      <span className="min-w-0 truncate text-slate-600">{label}</span>
      <span className="shrink-0 text-slate-300">·</span>
      <span className="shrink-0 tabular-nums">{compactRange}</span>
    </div>
  );
}

function formatCompactTimelineLabel(ms: number) {
  const safe = Math.max(0, Math.trunc(ms));
  const totalSeconds = Math.floor(safe / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
    2,
    "0",
  )}`;
}
