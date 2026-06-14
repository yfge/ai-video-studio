"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import { getString } from "@/hooks/useEpisodeDetail";
import type { TimelineResolvedVideoItem } from "@/utils/api/types";
import {
  formatTimelineMs,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import {
  timelineClipVideoStatus,
  timelineClipVideoStatusFromResolvedVideo,
} from "./EpisodeTimelineRenderModel";

export function ClipProductionSummary({
  item,
  track,
  selectedStoryboard,
  resolvedVideo,
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  selectedStoryboard: Record<string, unknown> | null;
  resolvedVideo?: TimelineResolvedVideoItem | null;
}) {
  if (!item) {
    return <div className="text-sm text-gray-500">请选择时间轴片段。</div>;
  }
  const meta = timelineItemMeta(item);
  const videoStatus =
    timelineClipVideoStatusFromResolvedVideo(resolvedVideo ?? null) ??
    timelineClipVideoStatus(meta, selectedStoryboard);
  const videoStatusLabel = videoStatus.ready
    ? `已关联 · ${videoStatus.source || "素材"}`
    : videoStatus.reason === "generating"
    ? "视频生成中"
    : "缺少视频素材";
  const videoStatusShortLabel = videoStatus.ready
    ? "已关联"
    : videoStatus.reason === "generating"
    ? "生成中"
    : "缺视频";
  const compactClipLabel = item.displayLabel || item.label || "片段";
  const reviewStatusLabel = getString(meta.status) || "待复核";
  return (
    <div
      data-clip-production-summary="true"
      data-clip-production-summary-layout="inline-identity"
      className="flex min-w-0 items-center gap-2 text-xs max-[760px]:block"
    >
      <div className="min-w-0 flex-1">
        <div
          data-clip-production-kicker="current-video"
          data-clip-production-kicker-layout="title-first"
          className="flex min-w-0 items-center gap-2 max-[760px]:gap-1.5"
        >
          <span
            data-clip-type-badge="neutral"
            data-clip-type-badge-visibility="sr-only"
            className="sr-only"
          >
            当前{track?.label || "片段"}
          </span>
          <span
            data-clip-production-mobile-label="true"
            title={item.label || compactClipLabel}
            className="hidden min-w-0 max-w-[5rem] truncate text-[11px] font-medium text-slate-600 max-[760px]:inline"
          >
            {compactClipLabel}
          </span>
          <span
            data-clip-production-title="full"
            title={item.label || compactClipLabel}
            className="min-w-0 max-w-[4.5rem] shrink-0 truncate text-sm font-semibold leading-5 text-gray-950 max-[760px]:sr-only"
          >
            {compactClipLabel}
          </span>
          <ClipVideoStatusLabel
            label={videoStatusShortLabel}
            title={videoStatusLabel}
            ready={videoStatus.ready}
            reason={videoStatus.reason}
          />
          <span
            data-clip-production-meta="true"
            title={`片段时间 ${formatTimelineMs(
              item.startMs,
            )} - ${formatTimelineMs(item.endMs)} · ${reviewStatusLabel}`}
            className="flex min-w-0 shrink-0 items-center gap-x-2 text-[11px] text-gray-500 max-[760px]:sr-only"
          >
            <span className="font-mono">
              {formatTimelineMs(item.startMs)} - {formatTimelineMs(item.endMs)}
            </span>
            <span
              data-clip-production-review-status="sr-only"
              className="sr-only"
            >
              {reviewStatusLabel}
            </span>
          </span>
          <span className="font-mono">
            <span
              data-clip-production-mobile-time="true"
              className="hidden min-w-0 truncate text-[11px] text-gray-500 max-[760px]:inline"
            >
              {formatTimelineMs(item.startMs)}-{formatTimelineMs(item.endMs)}
            </span>
          </span>
        </div>
      </div>
      <ClipVideoPreview
        url={videoStatus.url || null}
        label="播放选中片段视频"
      />
    </div>
  );
}

function ClipVideoStatusLabel({
  label,
  title,
  ready,
  reason,
}: {
  label: string;
  title: string;
  ready: boolean;
  reason?: string | null;
}) {
  const state = ready
    ? "ready"
    : reason === "generating"
    ? "generating"
    : "missing";
  return (
    <span
      title={title}
      data-clip-video-status="inline"
      data-clip-video-state={state}
      className={`inline-flex items-center gap-1 whitespace-nowrap text-[11px] font-medium ${
        state === "ready"
          ? "text-green-700"
          : state === "generating"
          ? "text-blue-700"
          : "text-amber-700"
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${
          state === "ready"
            ? "bg-green-500"
            : state === "generating"
            ? "bg-blue-500"
            : "bg-amber-500"
        }`}
      />
      {label}
    </span>
  );
}

function ClipVideoPreview({
  url,
  label,
}: {
  url: string | null;
  label: string;
}) {
  if (!url) return null;
  return (
    <video
      aria-label={label}
      className="h-16 w-36 rounded-md border border-gray-200 bg-black"
      controls
      preload="none"
      src={url}
    />
  );
}
