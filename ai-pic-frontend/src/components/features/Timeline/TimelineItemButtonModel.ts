import type { CSSProperties } from "react";
import { formatTimelineMs } from "./timelineScale";
import {
  minReadableTimelineItemWidth,
  resolveTimelineItemBackgroundColor,
  resolveTimelineItemBorderColor,
  resolveTimelineItemRingClass,
  resolveTimelineItemVisualTone,
  type TimelineItemVisualTone,
} from "./TimelineItemButtonVisualModel";
import type { TimelineItem } from "./TimelineTypes";

export type TimelineItemButtonModelInput = {
  item: TimelineItem;
  minStart: number;
  pxPerMs: number;
  selectedItemId?: string | null;
  trackId?: string;
  trackColor: string;
  trackHeight: number;
  labelOcclusionEndOffset?: number | null;
  zoom: number;
};

export type TimelineItemButtonModel = {
  ariaLabel: string;
  canShowAfterSelectedOverlap: boolean;
  isMarker: boolean;
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
  isSupportContextClip: boolean;
  labelOverlapInset: number;
  selectedRingClass: string;
  showLabel: boolean;
  style: CSSProperties;
  title: string;
  usesCompactTimelineLabel: boolean;
  visibleLabel: string;
  visualTone: TimelineItemVisualTone;
  width: number;
};

export function resolveTimelineItemButtonModel({
  item,
  minStart,
  pxPerMs,
  selectedItemId,
  trackId,
  trackColor,
  trackHeight,
  labelOcclusionEndOffset,
  zoom,
}: TimelineItemButtonModelInput): TimelineItemButtonModel {
  const startOffset = (item.startMs - minStart) * pxPerMs;
  const duration = Math.max(item.endMs - item.startMs, 0);
  const isMarker = duration <= 0;
  const isSelected = selectedItemId === item.id;
  const label = item.label || "";
  const displayLabel = item.displayLabel || label;
  const hasCompactLabel = Boolean(item.displayLabel);
  const isWholeEpisodeFit = zoom < 0.25;
  const isPrimaryProductionClip = item.type === "video" || trackId === "video";
  const isCompactPrimaryFit =
    isWholeEpisodeFit && isPrimaryProductionClip && trackHeight < 90;
  const minimumFittedVideoLabelWidth = 64;
  const isSupportContextClip =
    isWholeEpisodeFit && !isPrimaryProductionClip && !isSelected;
  const visualTone = resolveTimelineItemVisualTone({
    isPrimaryProductionClip,
    isSelected,
    isSupportContextClip,
  });
  const supportBackgroundColor = isSelected ? "#f1f5f9" : "#f8fafc";
  const supportBorderColor = isSelected ? "#94a3b8" : "#e2e8f0";
  const selectedRingClass = resolveTimelineItemRingClass({
    isPrimaryProductionClip,
    isSelected,
  });
  const rawWidth = duration * pxPerMs;
  const width = Math.max(
    rawWidth,
    isSelected
      ? isWholeEpisodeFit && isPrimaryProductionClip
        ? 54
        : isWholeEpisodeFit
        ? 24
        : 54
      : minReadableTimelineItemWidth({
          hasCompactLabel,
          isCompactPrimaryFit,
          isPrimaryProductionClip,
          isWholeEpisodeFit,
        }),
  );
  const labelOccludedBySelected =
    !isSelected &&
    isWholeEpisodeFit &&
    isPrimaryProductionClip &&
    labelOcclusionEndOffset != null &&
    startOffset < labelOcclusionEndOffset;
  const labelOverlapInset =
    labelOccludedBySelected && labelOcclusionEndOffset != null
      ? Math.max(0, labelOcclusionEndOffset - startOffset)
      : 0;
  const canShowAfterSelectedOverlap =
    labelOverlapInset > 0 && width - labelOverlapInset >= 18;
  const usesCompactTimelineLabel =
    isWholeEpisodeFit &&
    hasCompactLabel &&
    !isSelected &&
    !isPrimaryProductionClip &&
    width < 42;
  const visibleLabel =
    isWholeEpisodeFit && isSelected && isPrimaryProductionClip
      ? displayLabel
      : usesCompactTimelineLabel
      ? compactTimelineLabel(displayLabel)
      : displayLabel;
  const supportContextHeight = 8;
  const primaryTimelineBarHeight = isPrimaryProductionClip
    ? Math.min(trackHeight - 14, isSelected ? 44 : 38)
    : null;
  const verticalInset = isPrimaryProductionClip
    ? Math.max(7, (trackHeight - (primaryTimelineBarHeight ?? 0)) / 2)
    : isSupportContextClip
    ? Math.max(4, (trackHeight - supportContextHeight) / 2)
    : 5;
  const showWholeEpisodeLabel = isPrimaryProductionClip
    ? (isSelected && width >= 20) ||
      (hasCompactLabel &&
        rawWidth >= minimumFittedVideoLabelWidth &&
        width >= minimumFittedVideoLabelWidth) ||
      (!isCompactPrimaryFit && rawWidth >= 44 && canShowAfterSelectedOverlap) ||
      (!isCompactPrimaryFit && rawWidth >= 44)
    : isSelected && width >= 24;
  const showLabel =
    !isMarker &&
    (!labelOccludedBySelected || canShowAfterSelectedOverlap) &&
    (isWholeEpisodeFit
      ? showWholeEpisodeLabel
      : width >= (hasCompactLabel ? 40 : 64)) &&
    (hasCompactLabel ||
      isPrimaryProductionClip ||
      isSelected ||
      zoom >= 0.75) &&
    (visibleLabel.length <= 18 ||
      hasCompactLabel ||
      isSelected ||
      zoom >= 0.75);
  const itemStyleBase = {
    left: startOffset,
    top: verticalInset,
    height: isPrimaryProductionClip
      ? Math.max(28, primaryTimelineBarHeight ?? 38)
      : isSupportContextClip
      ? supportContextHeight
      : Math.max(14, trackHeight - verticalInset * 2),
    width,
  };

  return {
    ariaLabel: `在时间轴中选择 ${item.label || item.id}`,
    canShowAfterSelectedOverlap,
    isMarker,
    isPrimaryProductionClip,
    isSelected,
    isSupportContextClip,
    labelOverlapInset,
    selectedRingClass,
    showLabel,
    style: isMarker
      ? {
          ...itemStyleBase,
          backgroundColor: trackColor,
        }
      : {
          ...itemStyleBase,
          backgroundColor: resolveTimelineItemBackgroundColor({
            isPrimaryProductionClip,
            isSelected,
            isSupportContextClip,
            supportBackgroundColor,
          }),
          borderColor: resolveTimelineItemBorderColor({
            isPrimaryProductionClip,
            isSelected,
            isSupportContextClip,
            supportBorderColor,
          }),
          borderWidth: isSupportContextClip
            ? 0
            : isSelected && isPrimaryProductionClip
            ? 2
            : 1,
        },
    title: item.label
      ? `${item.label} (${formatTimelineMs(item.startMs)}–${formatTimelineMs(
          item.endMs,
        )})`
      : `${formatTimelineMs(item.startMs)}–${formatTimelineMs(item.endMs)}`,
    usesCompactTimelineLabel,
    visibleLabel,
    visualTone,
    width,
  };
}

function compactTimelineLabel(label: string) {
  return label.match(/\d+$/)?.[0] || label;
}
