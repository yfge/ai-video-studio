"use client";

import {
  resolveTimelineItemButtonModel,
  type TimelineItemButtonModelInput,
} from "./TimelineItemButtonModel";
import type { TimelineItem } from "./TimelineTypes";

export function TimelineItemButton({
  item,
  minStart,
  onSelect,
  pxPerMs,
  selectedItemId,
  trackId,
  trackColor,
  trackHeight,
  labelOcclusionEndOffset,
  zoom,
}: TimelineItemButtonModelInput & {
  onSelect?: (item: TimelineItem) => void;
}) {
  const model = resolveTimelineItemButtonModel({
    item,
    minStart,
    pxPerMs,
    selectedItemId,
    trackId,
    trackColor,
    trackHeight,
    labelOcclusionEndOffset,
    zoom,
  });

  return (
    <button
      data-timeline-item-id={item.id}
      data-timeline-item-type={item.type || trackId || "clip"}
      data-timeline-item-selected={model.isSelected ? "true" : "false"}
      data-timeline-label-visibility={model.showLabel ? "visible" : "hidden"}
      data-timeline-item-visual={
        model.isPrimaryProductionClip
          ? "timeline-bar"
          : model.isSupportContextClip
          ? "support-context"
          : "clip-block"
      }
      data-timeline-item-tone={model.visualTone}
      aria-label={model.ariaLabel}
      title={model.title}
      onClick={() => onSelect?.(item)}
      className={`absolute rounded-md ${model.isMarker ? "" : "border"} ${
        model.selectedRingClass
      } ${
        onSelect ? "cursor-pointer" : "cursor-default"
      } flex items-center overflow-hidden ${
        model.isPrimaryProductionClip && model.isSelected
          ? "shadow-sm shadow-blue-900/15"
          : model.isPrimaryProductionClip
          ? "shadow-[inset_0_0_0_1px_rgba(13,148,136,0.12),0_1px_2px_rgba(15,23,42,0.05)]"
          : "shadow-[inset_0_0_0_1px_rgba(15,23,42,0.04)]"
      }`}
      style={model.style}
    >
      <TimelineVideoClipFrame
        isMarker={model.isMarker}
        isPrimaryProductionClip={model.isPrimaryProductionClip}
        isSelected={model.isSelected}
      />
      <TimelineItemLabel model={model} />
    </button>
  );
}

function TimelineVideoClipFrame({
  isMarker,
  isPrimaryProductionClip,
  isSelected,
}: {
  isMarker: boolean;
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
}) {
  if (!isPrimaryProductionClip || isMarker) return null;
  const railTone = isSelected ? "selected" : "muted";
  const railClass = isSelected ? "bg-blue-600/60" : "bg-teal-400/35";

  return (
    <>
      <span
        data-timeline-video-clip-frame="filmstrip"
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 rounded-[inherit] bg-[linear-gradient(90deg,rgba(13,148,136,0.045)_0_1px,transparent_1px_10px),linear-gradient(180deg,rgba(255,255,255,0.94),rgba(20,184,166,0.035))]"
      />
      <span
        data-timeline-video-clip-rail="top"
        data-timeline-video-clip-rail-tone={railTone}
        aria-hidden="true"
        className={`pointer-events-none absolute left-0 right-0 top-0 h-2 ${railClass}`}
      />
      <span
        data-timeline-video-clip-rail="bottom"
        data-timeline-video-clip-rail-tone={railTone}
        aria-hidden="true"
        className={`pointer-events-none absolute bottom-0 left-0 right-0 h-2 ${railClass}`}
      />
      <span
        data-timeline-video-clip-spine="true"
        aria-hidden="true"
        className={`pointer-events-none absolute bottom-2 left-0 top-2 w-1 ${
          isSelected ? "bg-blue-600/75" : "bg-teal-500/45"
        }`}
      />
    </>
  );
}

function TimelineItemLabel({
  model,
}: {
  model: ReturnType<typeof resolveTimelineItemButtonModel>;
}) {
  if (!model.showLabel) return null;

  return (
    <span
      data-timeline-item-label-mode={
        model.usesCompactTimelineLabel ? "compact" : "full"
      }
      className={`relative z-10 text-[11px] ${
        model.usesCompactTimelineLabel
          ? "mx-auto min-w-4 rounded-sm bg-white/90 px-0.5 text-center tabular-nums shadow-[inset_0_0_0_1px_rgba(148,163,184,0.2)]"
          : `truncate ${
              model.canShowAfterSelectedOverlap ? "pr-1.5" : "px-1.5"
            }`
      } ${
        model.isPrimaryProductionClip
          ? model.isSelected
            ? "font-semibold text-slate-950"
            : "font-semibold text-slate-800"
          : "font-medium text-gray-700"
      }`}
      style={
        model.canShowAfterSelectedOverlap && !model.usesCompactTimelineLabel
          ? {
              paddingLeft: Math.min(
                model.labelOverlapInset + 5,
                model.width - 14,
              ),
            }
          : undefined
      }
    >
      {model.visibleLabel}
    </span>
  );
}
