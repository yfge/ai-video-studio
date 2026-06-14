export type TimelineItemVisualTone =
  | "primary-selected"
  | "primary-muted"
  | "support-context"
  | "support";

export function minReadableTimelineItemWidth({
  hasCompactLabel,
  isCompactPrimaryFit,
  isPrimaryProductionClip,
  isWholeEpisodeFit,
}: {
  hasCompactLabel: boolean;
  isCompactPrimaryFit: boolean;
  isPrimaryProductionClip: boolean;
  isWholeEpisodeFit: boolean;
}) {
  if (!isWholeEpisodeFit) return hasCompactLabel ? 46 : 8;
  if (!hasCompactLabel) return 8;
  if (!isPrimaryProductionClip) return 32;
  return isCompactPrimaryFit ? 10 : 24;
}

export function resolveTimelineItemVisualTone({
  isPrimaryProductionClip,
  isSelected,
  isSupportContextClip,
}: {
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
  isSupportContextClip: boolean;
}): TimelineItemVisualTone {
  if (isPrimaryProductionClip)
    return isSelected ? "primary-selected" : "primary-muted";
  return isSupportContextClip ? "support-context" : "support";
}

export function resolveTimelineItemRingClass({
  isPrimaryProductionClip,
  isSelected,
}: {
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
}) {
  if (!isSelected) return "";
  return isPrimaryProductionClip
    ? "z-20 ring-1 ring-blue-500/55 ring-offset-1"
    : "z-20 ring-1 ring-slate-300/70 ring-offset-0";
}

export function resolveTimelineItemBackgroundColor({
  isPrimaryProductionClip,
  isSelected,
  isSupportContextClip,
  supportBackgroundColor,
}: {
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
  isSupportContextClip: boolean;
  supportBackgroundColor: string;
}) {
  if (isSelected)
    return isPrimaryProductionClip ? "#dbeafe" : supportBackgroundColor;
  if (isPrimaryProductionClip) return "#f0fdfa";
  return isSupportContextClip
    ? "rgba(148, 163, 184, 0.18)"
    : supportBackgroundColor;
}

export function resolveTimelineItemBorderColor({
  isPrimaryProductionClip,
  isSelected,
  isSupportContextClip,
  supportBorderColor,
}: {
  isPrimaryProductionClip: boolean;
  isSelected: boolean;
  isSupportContextClip: boolean;
  supportBorderColor: string;
}) {
  if (isSelected)
    return isPrimaryProductionClip ? "#3b82f6" : supportBorderColor;
  if (isPrimaryProductionClip) return "#5eead4";
  return isSupportContextClip ? "transparent" : supportBorderColor;
}
