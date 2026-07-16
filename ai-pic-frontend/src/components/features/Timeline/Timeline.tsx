"use client";

import { useEffect, useMemo } from "react";
import {
  BASE_PX_PER_MS,
  buildTimelineTicks,
  resolveTimelineRange,
} from "./timelineScale";
import { TimelineCurrentTimeMarker } from "./TimelineCurrentTimeMarker";
import { TimelineGrid, TimelineTrackRows } from "./TimelineGrid";
import { TimelineOverview } from "./TimelineOverview";
import {
  findSelectedTimelineItem,
  TimelineSelectedMarker,
} from "./TimelineSelectedMarker";
import { TimelineSelectedContext } from "./TimelineSelectedContext";
import { TimelineToolbar } from "./TimelineToolbar";
import { timelineLayoutForMeasuredWidth } from "./timelineLayout";
import type { TimelineProps } from "./TimelineTypes";
import { useTimelineFitZoom } from "./useTimelineFitZoom";
export type {
  TimelineItem,
  TimelineProps,
  TimelineTrack,
} from "./TimelineTypes";

export function Timeline({
  tracks,
  startMs,
  endMs,
  currentTimeMs,
  onSelect,
  selectedItemId,
  initialZoom = 1,
  headerTitle,
  headerAction,
  fitToWidth = false,
}: TimelineProps) {
  const defaultLayout = timelineLayoutForMeasuredWidth(600);

  const { minStart, maxEnd } = useMemo(
    () => resolveTimelineRange(tracks, startMs, endMs),
    [endMs, startMs, tracks],
  );

  const totalMs = Math.max(1, maxEnd - minStart);
  const {
    maxZoom,
    measuredWidth,
    minZoom,
    resetZoom,
    setManualZoom,
    viewportRef,
    fitMode,
    zoom,
  } = useTimelineFitZoom({
    fitToWidth,
    initialZoom,
    totalMs,
    trackLabelWidth: defaultLayout.trackLabelWidth,
    trackRightPadding: defaultLayout.trackRightPadding,
  });
  const layout = timelineLayoutForMeasuredWidth(measuredWidth);
  const {
    compact,
    secondaryTrackHeight,
    tickLaneHeight,
    trackGap,
    trackHeight,
    trackLabelWidth,
    trackRightPadding,
  } = layout;
  const pxPerMs = BASE_PX_PER_MS * zoom;
  const trackHeights = tracks.map((track) =>
    track.id === "video" ? trackHeight : secondaryTrackHeight,
  );
  const trackStackHeight = trackHeights.reduce(
    (sum, height) => sum + height + trackGap,
    0,
  );
  const contentWidth = Math.max(
    measuredWidth,
    trackLabelWidth + totalMs * pxPerMs + trackRightPadding,
  );
  const ticks = useMemo(
    () => buildTimelineTicks(minStart, maxEnd),
    [maxEnd, minStart],
  );
  const selectedTimelineItem = useMemo(
    () => findSelectedTimelineItem(tracks, selectedItemId),
    [selectedItemId, tracks],
  );
  const selectedTrack = selectedTimelineItem
    ? tracks[selectedTimelineItem.trackIndex] ?? null
    : null;
  const primaryTrack =
    tracks.find((track) => track.id === "video") ??
    tracks.find((track) => track.items.some((item) => item.type === "video")) ??
    tracks[0] ??
    null;

  useEffect(() => {
    const viewport = viewportRef.current;
    const selectedItem = selectedTimelineItem?.item;
    if (!viewport || !selectedItem) return;

    const itemLeft =
      trackLabelWidth + (selectedItem.startMs - minStart) * pxPerMs;
    const itemRight =
      trackLabelWidth + (selectedItem.endMs - minStart) * pxPerMs;
    const viewportLeft = viewport.scrollLeft;
    const viewportRight = viewportLeft + viewport.clientWidth;
    const labelGuard = trackLabelWidth + 16;

    if (
      itemLeft < viewportLeft + labelGuard ||
      itemRight > viewportRight - 48
    ) {
      const nextLeft = Math.max(0, itemLeft - labelGuard);
      if (typeof viewport.scrollTo === "function") {
        viewport.scrollTo({ left: nextLeft, behavior: "smooth" });
      } else {
        viewport.scrollLeft = nextLeft;
      }
    }
  }, [minStart, pxPerMs, selectedTimelineItem, trackLabelWidth, viewportRef]);

  return (
    <div
      data-timeline="workspace"
      data-timeline-canvas="true"
      data-timeline-density="primary"
      data-timeline-presence="explicit-production-time-axis"
      data-timeline-surface="dominant-workspace-axis"
      data-timeline-visibility-contract="first-screen-primary"
      data-timeline-visual-priority="main-time-axis"
      data-timeline-responsive-density={compact ? "compact" : "regular"}
      data-timeline-fit-to-width={fitToWidth ? "true" : "false"}
      data-timeline-scale-mode={fitMode}
      aria-label="时间轴导航：片段时间轴定位区"
      className="relative w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_10px_28px_rgba(15,23,42,0.07)]"
    >
      <TimelineToolbar
        fitToWidth={fitToWidth}
        fitMode={fitMode}
        headerAction={headerAction}
        headerTitle={headerTitle}
        selectedContext={
          <TimelineSelectedContext
            item={selectedTimelineItem?.item ?? null}
            track={selectedTrack}
          />
        }
        maxEnd={maxEnd}
        maxZoom={maxZoom}
        minStart={minStart}
        minZoom={minZoom}
        onResetZoom={resetZoom}
        onZoomChange={setManualZoom}
        primaryClipCount={primaryTrack?.items.length ?? 0}
        totalMs={totalMs}
        zoom={zoom}
      />
      <TimelineOverview
        compact={compact}
        maxEnd={maxEnd}
        minStart={minStart}
        onSelect={onSelect}
        selectedItemId={selectedItemId}
        tracks={tracks}
      />
      <div
        ref={viewportRef}
        data-timeline-viewport="lanes"
        data-timeline-scrollbar="subtle"
        data-timeline-scroll-mode={
          fitMode === "readable-window"
            ? "scrollable-readable-lanes"
            : "fit-to-viewport"
        }
        className="relative overflow-x-scroll border-t border-slate-200 bg-gradient-to-b from-white to-slate-50/80 pb-2"
        style={{ scrollbarGutter: "stable" }}
      >
        <div
          data-timeline-content="lanes"
          data-timeline-content-scale-mode={fitMode}
          className="relative"
          style={{
            width: `${contentWidth}px`,
            minHeight: `${tickLaneHeight + trackStackHeight + 6}px`,
          }}
        >
          <TimelineGrid
            minStart={minStart}
            pxPerMs={pxPerMs}
            tickLaneHeight={tickLaneHeight}
            ticks={ticks}
            trackLabelWidth={trackLabelWidth}
          />
          {selectedTimelineItem ? (
            <TimelineSelectedMarker
              contentWidth={contentWidth}
              item={selectedTimelineItem.item}
              minStart={minStart}
              pxPerMs={pxPerMs}
              tickLaneHeight={tickLaneHeight}
              trackLabelWidth={trackLabelWidth}
            />
          ) : null}
          <TimelineTrackRows
            minStart={minStart}
            onSelect={onSelect}
            pxPerMs={pxPerMs}
            selectedItemId={selectedItemId}
            trackGap={trackGap}
            trackHeight={trackHeight}
            trackHeights={trackHeights}
            tickLaneHeight={tickLaneHeight}
            trackLabelWidth={trackLabelWidth}
            trackRightPadding={trackRightPadding}
            tracks={tracks}
            zoom={zoom}
          />
          {currentTimeMs != null ? (
            <TimelineCurrentTimeMarker
              currentTimeMs={currentTimeMs}
              minStart={minStart}
              pxPerMs={pxPerMs}
              trackLabelWidth={trackLabelWidth}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
