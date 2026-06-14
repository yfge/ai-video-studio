import type { ReactNode } from "react";

export type TimelineItem = {
  id: string;
  startMs: number;
  endMs: number;
  label?: string;
  displayLabel?: string;
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
  headerTitle?: string;
  headerAction?: ReactNode;
  fitToWidth?: boolean;
};
