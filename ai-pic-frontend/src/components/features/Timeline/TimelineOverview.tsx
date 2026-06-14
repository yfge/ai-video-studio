"use client";

import { formatTimelineLabel } from "./timelineScale";
import type { TimelineItem, TimelineTrack } from "./TimelineTypes";

export function TimelineOverview({
  compact = false,
  maxEnd,
  minStart,
  onSelect,
  selectedItemId,
  tracks,
}: {
  compact?: boolean;
  maxEnd: number;
  minStart: number;
  onSelect?: (item: TimelineItem) => void;
  selectedItemId?: string | null;
  tracks: TimelineTrack[];
}) {
  const primaryTrack =
    tracks.find((track) => track.id === "video") ??
    tracks.find((track) => track.items.some((item) => item.type === "video")) ??
    tracks[0];
  if (!primaryTrack || !primaryTrack.items.length) return null;

  const totalMs = Math.max(1, maxEnd - minStart);
  const totalRangeLabel =
    minStart === 0
      ? `${formatTimelineLabel(totalMs)} · ${primaryTrack.items.length} 段`
      : `${formatTimelineLabel(minStart)}-${formatTimelineLabel(maxEnd)} · ${
          primaryTrack.items.length
        } 段`;
  const selectedItem = primaryTrack.items.find(
    (item) => item.id === selectedItemId,
  );
  const markerLeft = selectedItem
    ? percentForMs(
        selectedItem.startMs +
          Math.max(0, selectedItem.endMs - selectedItem.startMs) / 2,
        minStart,
        totalMs,
      )
    : null;
  const containerClass = compact
    ? "border-b border-slate-200 bg-slate-50/90 px-2 py-1.5"
    : "border-b border-slate-200 bg-slate-50/80 px-3 py-1.5";
  const gridClass = compact
    ? "grid grid-cols-[auto_minmax(0,1fr)] items-center gap-2"
    : "grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2";
  const railClass = compact
    ? "relative h-7 overflow-hidden rounded-md border border-slate-300 bg-white shadow-inner shadow-slate-200/80"
    : "relative h-8 overflow-hidden rounded-md border border-slate-300 bg-white shadow-inner shadow-slate-200/80";
  const itemHeightClass = compact ? "h-4" : "h-5";

  return (
    <div
      data-timeline-overview="true"
      data-timeline-overview-density="primary-navigation"
      data-timeline-overview-layout="visible-overview-axis"
      data-timeline-overview-role="full-episode-time-axis"
      data-timeline-overview-responsive-density={
        compact ? "compact" : "regular"
      }
      data-timeline-overview-visibility="full-episode-context-rail"
      className={containerClass}
    >
      <div className={gridClass}>
        <div
          data-timeline-overview-track-label={primaryTrack.id}
          data-timeline-overview-track-label-visibility="visible"
          className="whitespace-nowrap text-[11px] font-extrabold leading-none text-blue-800"
          title={`全片时间轴 · ${primaryTrack.label}`}
        >
          总览
          <span className="sr-only">全片概览</span>
          <span className="sr-only">全片时间轴</span>
        </div>
        <div data-timeline-overview-rail="true" className={railClass}>
          <div
            aria-hidden="true"
            className="absolute left-0 top-0 h-full w-px bg-slate-300"
          />
          <div
            aria-hidden="true"
            className="absolute right-0 top-0 h-full w-px bg-slate-300"
          />
          {primaryTrack.items.map((item, index) => {
            const left = percentForMs(item.startMs, minStart, totalMs);
            const width = Math.max(
              0.35,
              ((Math.max(item.endMs, item.startMs) - item.startMs) / totalMs) *
                100,
            );
            const isSelected = selectedItemId === item.id;
            return (
              <button
                key={item.id}
                type="button"
                data-timeline-overview-item={item.type || primaryTrack.id}
                aria-label={`在全片概览中选择 ${
                  item.label || `片段 ${index + 1}`
                }`}
                title={`${
                  item.label || `片段 ${index + 1}`
                } ${formatTimelineLabel(item.startMs)}-${formatTimelineLabel(
                  item.endMs,
                )}`}
                onClick={() => onSelect?.(item)}
                className={`absolute top-1/2 ${itemHeightClass} -translate-y-1/2 rounded-sm border ${
                  isSelected
                    ? "border-blue-900 bg-blue-600 shadow-sm shadow-blue-900/20"
                    : "border-teal-200/80 bg-teal-50/80 hover:bg-teal-100/70"
                }`}
                style={{
                  left: `${left}%`,
                  minWidth: isSelected ? (compact ? 6 : 8) : 4,
                  width: `${Math.min(width, 100 - left)}%`,
                }}
              />
            );
          })}
          {markerLeft != null ? (
            <div
              data-timeline-overview-selected-marker="true"
              className="pointer-events-none absolute bottom-0 top-0 w-px bg-blue-700/70"
              style={{ left: `${markerLeft}%` }}
            >
              <span className="sr-only">当前片段位置</span>
            </div>
          ) : null}
        </div>
        <div
          data-timeline-overview-range-visibility={
            compact ? "sr-only" : "visible"
          }
          className={
            compact
              ? "sr-only"
              : "whitespace-nowrap text-right text-[10px] font-medium text-slate-500"
          }
        >
          {totalRangeLabel}
        </div>
      </div>
    </div>
  );
}

function percentForMs(value: number, minStart: number, totalMs: number) {
  return Math.min(100, Math.max(0, ((value - minStart) / totalMs) * 100));
}
