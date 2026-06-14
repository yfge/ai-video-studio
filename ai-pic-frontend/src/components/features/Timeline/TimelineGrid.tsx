"use client";

import { TimelineItemButton } from "./TimelineItemButton";
import type { Tick } from "./timelineScale";
import type { TimelineItem, TimelineTrack } from "./TimelineTypes";

export function TimelineGrid({
  minStart,
  pxPerMs,
  tickLaneHeight,
  ticks,
  trackLabelWidth,
}: {
  minStart: number;
  pxPerMs: number;
  tickLaneHeight: number;
  ticks: Tick[];
  trackLabelWidth: number;
}) {
  return (
    <>
      <div
        data-timeline-grid="true"
        aria-hidden="true"
        className="absolute inset-0"
      >
        {ticks.map((tick) => {
          const left = trackLabelWidth + (tick.positionMs - minStart) * pxPerMs;
          return (
            <div
              key={`grid-${tick.positionMs}`}
              data-timeline-grid-line-depth="ruler-fade"
              className="absolute bottom-0 top-0 w-px bg-gradient-to-b from-slate-300/80 via-slate-200/25 to-transparent"
              style={{ left }}
            />
          );
        })}
      </div>
      <div
        data-timeline-axis-line="true"
        aria-hidden="true"
        className="pointer-events-none absolute left-0 right-0 z-20 border-b-2 border-blue-500/70 shadow-[0_1px_0_rgba(37,99,235,0.14)]"
        style={{ top: tickLaneHeight - 1 }}
      />
      <div
        data-timeline-ruler="true"
        data-timeline-ruler-visual="timecode-axis"
        className="absolute left-0 right-0 top-0 z-10 border-b border-slate-200 bg-slate-50/90"
        style={{ height: tickLaneHeight }}
      >
        <div
          data-timeline-ruler-origin="true"
          data-timeline-ruler-origin-layout="timeline-axis-label"
          className="sticky left-0 top-0 z-30 flex h-full flex-col justify-center border-r border-blue-200 bg-white px-1.5 text-left leading-tight text-blue-800 shadow-[inset_4px_0_0_rgba(37,99,235,0.88),1px_0_0_rgba(148,163,184,0.18)]"
          style={{ width: trackLabelWidth }}
        >
          <span
            data-timeline-ruler-origin-primary="true"
            className="text-[10px] font-extrabold"
          >
            时间轴
          </span>
          <span
            data-timeline-ruler-origin-secondary="true"
            className="text-[9px] font-semibold text-slate-500"
          >
            刻度
          </span>
        </div>
        {ticks.map((tick) => {
          const left = trackLabelWidth + (tick.positionMs - minStart) * pxPerMs;
          return (
            <div
              key={tick.positionMs}
              data-timeline-tick={tick.label}
              className="absolute top-0 flex h-full flex-col items-center border-l border-slate-300/70 pt-1.5 text-[10px] font-bold text-slate-800"
              style={{ left }}
            >
              <span className="rounded-sm bg-white px-1 shadow-[inset_0_0_0_1px_rgba(59,130,246,0.22)]">
                {tick.label}
              </span>
            </div>
          );
        })}
      </div>
    </>
  );
}

export function TimelineTrackRows({
  minStart,
  onSelect,
  pxPerMs,
  selectedItemId,
  trackGap,
  trackHeight,
  trackHeights,
  tickLaneHeight,
  trackLabelWidth,
  trackRightPadding,
  tracks,
  zoom,
}: {
  minStart: number;
  onSelect?: (item: TimelineItem) => void;
  pxPerMs: number;
  selectedItemId?: string | null;
  trackGap: number;
  trackHeight: number;
  trackHeights: number[];
  tickLaneHeight: number;
  trackLabelWidth: number;
  trackRightPadding: number;
  tracks: TimelineTrack[];
  zoom: number;
}) {
  return (
    <div className="absolute left-0 right-0" style={{ top: tickLaneHeight }}>
      {tracks.map((track, index) => {
        const color = track.color || "#2563eb";
        const isVideoTrack = track.id === "video";
        const laneHeight = trackHeights[index] ?? trackHeight;
        const selectedItem = isVideoTrack
          ? track.items.find((item) => item.id === selectedItemId)
          : null;
        const selectedCoverEndOffset = selectedItem
          ? selectedItemCoverEndOffset(selectedItem, minStart, pxPerMs)
          : null;
        return (
          <div
            key={track.id}
            data-track-id={track.id}
            data-timeline-track-row={track.id}
            data-timeline-primary-lane={
              isVideoTrack ? "video-production" : undefined
            }
            data-timeline-primary-lane-visual={
              isVideoTrack ? "dominant-time-axis" : undefined
            }
            data-timeline-support-lane-density={
              isVideoTrack ? undefined : "reference-strip"
            }
            className={`relative border-t ${
              isVideoTrack
                ? "border-y border-slate-400 bg-white shadow-[inset_0_1px_0_rgba(15,23,42,0.09),inset_0_-1px_0_rgba(15,23,42,0.07)]"
                : "border-slate-100 bg-white/50"
            }`}
            style={{ minHeight: laneHeight, marginBottom: trackGap }}
          >
            <div
              data-timeline-track-label={track.id}
              data-timeline-track-label-visual={
                isVideoTrack ? "primary-axis" : "support-muted"
              }
              className={`sticky left-0 top-0 z-20 flex items-center gap-1.5 border-r px-1.5 ${
                isVideoTrack
                  ? "border-slate-200 bg-white text-[12px] font-bold text-slate-900 shadow-[inset_4px_0_0_rgba(20,184,166,0.72),1px_0_0_rgba(148,163,184,0.18)]"
                  : "border-transparent bg-transparent text-[10px] font-medium text-slate-400"
              }`}
              style={{ height: laneHeight, width: trackLabelWidth }}
            >
              <span
                data-timeline-track-marker={
                  isVideoTrack ? "primary" : "support"
                }
                className={`inline-block rounded-full ${
                  isVideoTrack
                    ? "h-3 w-3 ring-2 ring-teal-100"
                    : "h-px w-1.5 bg-slate-200"
                }`}
                style={isVideoTrack ? { backgroundColor: color } : undefined}
              ></span>
              {isVideoTrack ? (
                <span className="flex min-w-0 flex-col leading-tight">
                  <span>{track.label}</span>
                  <span
                    data-timeline-primary-lane-label="visible"
                    className="text-[9px] font-semibold text-slate-500"
                  >
                    主时间轴
                  </span>
                </span>
              ) : (
                track.label
              )}
              {isVideoTrack ? <span className="sr-only">主线</span> : null}
            </div>
            <div
              className="absolute bottom-0 top-0 overflow-visible"
              style={{
                left: trackLabelWidth,
                right: trackRightPadding,
              }}
            >
              {isVideoTrack ? (
                <div
                  data-timeline-video-axis-line="true"
                  aria-hidden="true"
                  className="pointer-events-none absolute left-0 right-0 top-1/2 h-7 -translate-y-1/2 border-y border-teal-500/35 bg-teal-500/20 shadow-[0_0_0_1px_rgba(13,148,136,0.28)]"
                />
              ) : null}
              {track.items.map((item) => (
                <TimelineItemButton
                  key={item.id}
                  item={item}
                  minStart={minStart}
                  onSelect={onSelect}
                  pxPerMs={pxPerMs}
                  selectedItemId={selectedItemId}
                  trackId={track.id}
                  trackColor={color}
                  trackHeight={laneHeight}
                  labelOcclusionEndOffset={selectedCoverEndOffset}
                  zoom={zoom}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function selectedItemCoverEndOffset(
  item: TimelineItem,
  minStart: number,
  pxPerMs: number,
) {
  const startOffset = (item.startMs - minStart) * pxPerMs;
  const width = Math.max(Math.max(item.endMs - item.startMs, 0) * pxPerMs, 54);
  return startOffset + width;
}
