export type TimelineLayoutMetrics = {
  compact: boolean;
  secondaryTrackHeight: number;
  tickLaneHeight: number;
  trackGap: number;
  trackHeight: number;
  trackLabelWidth: number;
  trackRightPadding: number;
};

export const TIMELINE_COMPACT_WIDTH = 520;

export function timelineLayoutForMeasuredWidth(
  measuredWidth: number,
): TimelineLayoutMetrics {
  const compact = measuredWidth > 0 && measuredWidth < TIMELINE_COMPACT_WIDTH;
  return {
    compact,
    secondaryTrackHeight: compact ? 16 : 18,
    tickLaneHeight: 44,
    trackGap: compact ? 1 : 2,
    trackHeight: compact ? 104 : 116,
    trackLabelWidth: compact ? 88 : 112,
    trackRightPadding: 8,
  };
}
