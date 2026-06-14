"use client";

import { useMemo } from "react";
import {
  Timeline,
  type TimelineItem,
  type TimelineTrack,
} from "@/components/features";
import type { TimelineResponse } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import { buildEpisodeTimelineTracks } from "./EpisodeTimelineWorkspaceModel";
import type { StoryboardTimelineOverview } from "./WorkspaceStoryboardTimelineOverviewModel";

export function WorkspaceStoryboardTimelinePanel({
  episodeKey,
  selectedScriptId,
  selectedTimelineSpec,
  selectedAudioTimeline,
  selectedStoryboard,
  overview,
}: {
  episodeKey: string;
  selectedScriptId?: number | null;
  selectedTimelineSpec?: TimelineResponse | null;
  selectedAudioTimeline?: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  overview: StoryboardTimelineOverview;
}) {
  const tracks = useMemo(
    () =>
      buildEpisodeTimelineTracks(
        selectedTimelineSpec ?? null,
        selectedAudioTimeline ?? null,
        selectedStoryboard,
      ),
    [selectedAudioTimeline, selectedStoryboard, selectedTimelineSpec],
  );
  const timelineTracks = tracks.length ? tracks : EMPTY_SUPPORT_TIMELINE_TRACKS;
  const selectedItemId = useMemo(
    () => firstVideoTimelineItemId(tracks),
    [tracks],
  );

  const handleSelectTimelineItem = (item: TimelineItem) => {
    const clipId = timelineClipIdFromItem(item);
    const href = episodeWorkspaceHref(episodeKey, {
      tab: "timeline",
      scriptId: selectedScriptId,
      extraParams: clipId ? { clipId } : undefined,
    });
    window.location.assign(href);
  };

  return (
    <div data-storyboard-support-timeline="true" className="mt-4 space-y-3">
      <Timeline
        tracks={timelineTracks}
        selectedItemId={tracks.length ? selectedItemId : null}
        onSelect={tracks.length ? handleSelectTimelineItem : undefined}
        startMs={tracks.length ? undefined : 0}
        endMs={tracks.length ? undefined : 10000}
        initialZoom={1}
        fitToWidth
        headerTitle="全片时间轴"
      />
      <div
        data-storyboard-support-timeline-summary="true"
        data-storyboard-support-timeline-summary-layout="compact-strip"
        className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-t border-slate-200 bg-slate-50/60 px-3 py-2 text-xs text-slate-600"
      >
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
          <span className="font-semibold text-slate-900">
            {overview.timelineLabel}
          </span>
          <span>状态 {overview.status ?? "未知"}</span>
          <span>时长 {overview.durationLabel}</span>
          <span>{overview.trackSummary}</span>
          <span>对白 {overview.dialogueClipCount}</span>
          <span>视频 {overview.videoClipCount}</span>
          {overview.audioVersion ? (
            <span>音频 v{overview.audioVersion}</span>
          ) : null}
        </div>
        {overview.audioUrl ? (
          <details
            data-storyboard-support-audio="collapsed"
            className="group relative"
          >
            <summary className="flex h-6 cursor-pointer list-none items-center rounded px-1.5 text-xs font-medium text-slate-600 hover:bg-white hover:text-slate-900 marker:hidden [&::-webkit-details-marker]:hidden">
              音轨
            </summary>
            <div className="absolute right-0 top-full z-20 mt-1 w-80 rounded-md border border-slate-200 bg-white p-2 shadow-lg">
              <audio
                aria-label="播放时间轴音轨"
                className="w-full"
                controls
                preload="none"
                src={overview.audioUrl}
              />
            </div>
          </details>
        ) : (
          <span className="text-amber-700">暂无可播放音轨 URL</span>
        )}
      </div>
    </div>
  );
}

const EMPTY_SUPPORT_TIMELINE_TRACKS: TimelineTrack[] = [
  {
    id: "video",
    label: "视频",
    color: "#0f766e",
    items: [],
  },
];

function firstVideoTimelineItemId(tracks: TimelineTrack[]) {
  return tracks.find((track) => track.id === "video")?.items[0]?.id ?? null;
}

function timelineClipIdFromItem(item: TimelineItem) {
  const meta = item.meta ?? {};
  const rawClipId =
    stringValue(meta.clip_id) ??
    stringValue(meta.timeline_clip_id) ??
    stringValue(meta.id);
  if (rawClipId) return rawClipId;
  if (item.type && item.id.startsWith(`${item.type}-`)) {
    return item.id.slice(item.type.length + 1);
  }
  return item.id;
}

function stringValue(value: unknown) {
  return typeof value === "string" && value.trim() ? value : null;
}
