"use client";

import { useMemo, useState } from "react";
import {
  BASE_PX_PER_MS,
  buildTimelineTicks,
  clamp,
  formatTimelineMs,
  resolveTimelineRange,
} from "./timelineScale";

export type TimelineItem = {
  id: string;
  startMs: number;
  endMs: number;
  label?: string;
  color?: string;
  type?: string;
  meta?: Record<string, unknown>;
};

export type TimelineTrack = {
  id: string;
  label: string;
  color?: string;
  items: TimelineItem[];
};

export type TimelineProps = {
  tracks: TimelineTrack[];
  startMs?: number;
  endMs?: number;
  currentTimeMs?: number;
  onSelect?: (item: TimelineItem) => void;
  selectedItemId?: string | null;
  initialZoom?: number;
};

export function Timeline({
  tracks,
  startMs,
  endMs,
  currentTimeMs,
  onSelect,
  selectedItemId,
  initialZoom = 1,
}: TimelineProps) {
  const [zoom, setZoom] = useState(clamp(initialZoom, 0.25, 4));

  const { minStart, maxEnd } = useMemo(
    () => resolveTimelineRange(tracks, startMs, endMs),
    [endMs, startMs, tracks],
  );

  const totalMs = Math.max(1, maxEnd - minStart);
  const pxPerMs = BASE_PX_PER_MS * zoom;
  const contentWidth = Math.max(600, totalMs * pxPerMs);
  const ticks = useMemo(
    () => buildTimelineTicks(minStart, maxEnd),
    [maxEnd, minStart],
  );

  const colorForTrack = (track: TimelineTrack) => track.color || "#2563eb";

  const renderItem = (item: TimelineItem, trackColor: string) => {
    const startOffset = (item.startMs - minStart) * pxPerMs;
    const duration = Math.max(item.endMs - item.startMs, 0);
    const width = Math.max(duration * pxPerMs, 6);
    const isMarker = duration <= 0;
    const isSelected = selectedItemId === item.id;
    const style = isMarker
      ? {
          left: startOffset,
          width: 6,
          backgroundColor: trackColor,
        }
      : {
          left: startOffset,
          width,
          backgroundColor: `${trackColor}22`,
          borderColor: trackColor,
          borderWidth: 1,
        };
    return (
      <button
        key={item.id}
        title={
          item.label
            ? `${item.label} (${formatTimelineMs(
                item.startMs,
              )}–${formatTimelineMs(item.endMs)})`
            : `${formatTimelineMs(item.startMs)}–${formatTimelineMs(
                item.endMs,
              )}`
        }
        onClick={() => onSelect?.(item)}
        className={`absolute bottom-1 top-1 rounded-sm ${
          isMarker ? "" : "border"
        } ${isSelected ? "ring-2 ring-blue-500 ring-offset-1" : ""} ${
          onSelect ? "cursor-pointer" : "cursor-default"
        } overflow-hidden`}
        style={style}
      >
        {!isMarker ? (
          <span className="px-1 text-[11px] text-gray-800 truncate">
            {item.label}
          </span>
        ) : null}
      </button>
    );
  };

  return (
    <div className="w-full rounded-md border border-gray-200 bg-white">
      <div className="flex items-center justify-between px-3 py-2 text-xs text-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-gray-500">
            时间轴窗口 {formatTimelineMs(minStart)} – {formatTimelineMs(maxEnd)}
          </span>
          <span className="text-[11px] text-gray-500">
            时长 {(totalMs / 1000).toFixed(1)}s
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-500">缩放</span>
          <input
            type="range"
            min={0.25}
            max={4}
            step={0.05}
            value={zoom}
            onChange={(e) =>
              setZoom(clamp(Number.parseFloat(e.target.value), 0.25, 4))
            }
          />
          <button
            type="button"
            onClick={() => setZoom(1)}
            className="rounded-md border border-gray-200 px-2 py-1 text-[11px] text-gray-700 hover:bg-gray-50"
          >
            1x
          </button>
        </div>
      </div>
      <div className="relative overflow-x-auto border-t border-gray-200">
        <div
          className="relative"
          style={{
            width: `${contentWidth}px`,
            minHeight: `${60 + tracks.length * 42}px`,
          }}
        >
          <div className="absolute left-0 right-0 top-0 h-8">
            {ticks.map((tick) => {
              const left = (tick.positionMs - minStart) * pxPerMs;
              return (
                <div
                  key={tick.positionMs}
                  className="absolute top-0 flex flex-col items-center text-[10px] text-gray-400"
                  style={{ left }}
                >
                  <div className="h-2 w-px bg-gray-300" />
                  <span>{tick.label}</span>
                </div>
              );
            })}
          </div>
          <div className="absolute left-0 right-0 top-8">
            {tracks.map((track) => {
              const color = colorForTrack(track);
              return (
                <div
                  key={track.id}
                  className="relative mb-3 border-t border-gray-100 bg-white pt-1"
                  style={{ minHeight: 40 }}
                >
                  <div className="absolute left-0 top-2 flex h-5 items-center gap-2 pl-1 text-[12px] text-gray-700">
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ backgroundColor: color }}
                    ></span>
                    {track.label}
                  </div>
                  <div className="relative ml-24 mr-2 h-8 overflow-visible">
                    {track.items.map((item) => renderItem(item, color))}
                  </div>
                </div>
              );
            })}
          </div>
          {currentTimeMs != null ? (
            <div
              className="pointer-events-none absolute top-0 bottom-0 border-l-2 border-blue-500/70"
              style={{ left: (currentTimeMs - minStart) * pxPerMs }}
            >
              <div className="absolute -top-5 -translate-x-1/2 rounded bg-blue-500 px-1 py-0.5 text-[10px] text-white">
                {formatTimelineMs(currentTimeMs)}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
