import type { TimelineTrack } from "./Timeline";

export type Tick = { positionMs: number; label: string };

export const BASE_PX_PER_MS = 0.05;

export const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

export const formatTimelineMs = (ms: number) => {
  const safe = Math.max(0, Math.trunc(ms));
  const totalSeconds = Math.floor(safe / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const millis = safe % 1000;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
    2,
    "0",
  )}.${String(millis).padStart(3, "0")}`;
};

export const formatTimelineLabel = (ms: number) =>
  formatTimelineMs(ms).replace(/\.000$/, "");

const niceStep = (rangeMs: number) => {
  const candidates = [
    100, 200, 250, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000,
  ];
  const target = rangeMs / 8;
  for (const step of candidates) {
    if (step >= target) return step;
  }
  return candidates[candidates.length - 1];
};

export const buildTimelineTicks = (startMs: number, endMs: number): Tick[] => {
  if (endMs <= startMs) return [];
  const step = niceStep(endMs - startMs);
  const ticks: Tick[] = [];
  const first = Math.ceil(startMs / step) * step;
  for (let t = first; t <= endMs; t += step) {
    ticks.push({ positionMs: t, label: formatTimelineLabel(t) });
  }
  return ticks;
};

export const resolveTimelineRange = (
  tracks: TimelineTrack[],
  startMs?: number,
  endMs?: number,
) => {
  const minStart =
    startMs ??
    tracks.reduce((acc, track) => {
      track.items.forEach((item) => {
        acc = Math.min(acc, item.startMs);
      });
      return acc;
    }, Number.POSITIVE_INFINITY);
  const maxEnd =
    endMs ??
    tracks.reduce((acc, track) => {
      track.items.forEach((item) => {
        acc = Math.max(acc, item.endMs ?? item.startMs);
      });
      return acc;
    }, Number.NEGATIVE_INFINITY);
  const safeMin = Number.isFinite(minStart) ? minStart : 0;
  const safeMax = Number.isFinite(maxEnd) ? maxEnd : safeMin + 10000;
  return { minStart: safeMin, maxEnd: Math.max(safeMax, safeMin + 1000) };
};
