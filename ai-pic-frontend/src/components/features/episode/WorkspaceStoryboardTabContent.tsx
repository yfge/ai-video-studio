"use client";

import { useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
} from "@/components/shared";
import { firstTimelineVideoClipId } from "@/hooks/episode/timelineClipUtils";
import type {
  NormalizedScene,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
} from "./WorkspaceStoryboardSupportModel";
import { WorkspaceStoryboardActions } from "./WorkspaceStoryboardActions";
import { WorkspaceStoryboardClipManagement } from "./WorkspaceStoryboardClipManagement";
import { StoryboardSupportFrameRow } from "./WorkspaceStoryboardFrameRow";
import { WorkspaceStoryboardTimelinePanel } from "./WorkspaceStoryboardTimelinePanel";
import { buildStoryboardTimelineOverview } from "./WorkspaceStoryboardTimelineOverviewModel";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

interface WorkspaceStoryboardTabContentProps {
  episodeKey?: string;
  selectedScriptId?: number | null;
  hasStoryboard?: boolean;
  selectedAudioTimeline?: Record<string, unknown> | null;
  selectedTimelineSpec?: TimelineResponse | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  showAlert?: ShowAlert;
}

export function WorkspaceStoryboardTabContent({
  episodeKey = "",
  selectedScriptId,
  hasStoryboard,
  selectedAudioTimeline,
  selectedTimelineSpec,
  onTimelineUpdated,
  resolvedVideos,
  selectedStoryboard,
  normalizedScenes,
  showAlert,
}: WorkspaceStoryboardTabContentProps) {
  const [localTimelineSpec, setLocalTimelineSpec] =
    useState<TimelineResponse | null>(selectedTimelineSpec ?? null);
  useEffect(() => {
    setLocalTimelineSpec(selectedTimelineSpec ?? null);
  }, [selectedTimelineSpec]);
  const handleTimelineUpdated = (timeline: TimelineResponse) => {
    setLocalTimelineSpec(timeline);
    onTimelineUpdated?.(timeline);
  };
  const timelineHref = episodeWorkspaceHref(episodeKey, {
    tab: "timeline",
    scriptId: selectedScriptId,
  });
  const summary = buildStoryboardSupportSummary(
    selectedStoryboard,
    localTimelineSpec,
  );
  const timelineOverview = buildStoryboardTimelineOverview(
    localTimelineSpec,
    selectedAudioTimeline,
  );
  const firstVideoClipId = firstTimelineVideoClipId(localTimelineSpec);
  const frames = buildStoryboardSupportFrames(
    selectedStoryboard,
    normalizedScenes,
    localTimelineSpec,
  );
  const storyboardStatus = frames.length
    ? "已有占位"
    : hasStoryboard
    ? "待补占位"
    : "待生成占位";

  return (
    <div className="space-y-4">
      <section
        data-storyboard-support-shell="unframed"
        className="border-b border-slate-200 bg-white"
      >
        <OperatorSectionHeader
          title="分镜辅助工作区"
          subtitle="按视频片段汇总分镜、首尾帧和视频状态"
          action={
            <WorkspaceStoryboardActions
              selectedScriptId={selectedScriptId}
              selectedAudioTimeline={selectedAudioTimeline}
              timelineHref={timelineHref}
              clipStoryboardHref={
                firstVideoClipId
                  ? episodeWorkspaceHref(episodeKey, {
                      tab: "timeline",
                      scriptId: selectedScriptId,
                      extraParams: { clipId: firstVideoClipId },
                    })
                  : null
              }
              showAlert={showAlert}
            />
          }
        />
        {timelineOverview ? (
          <WorkspaceStoryboardTimelinePanel
            episodeKey={episodeKey}
            selectedScriptId={selectedScriptId}
            selectedTimelineSpec={localTimelineSpec}
            selectedAudioTimeline={selectedAudioTimeline}
            selectedStoryboard={selectedStoryboard}
            overview={timelineOverview}
          />
        ) : null}
        <div
          data-storyboard-support-context-strip="inline"
          className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-100 bg-slate-50/50 px-3 py-1.5 text-xs text-slate-600"
        >
          <SupportMetaItem
            label="来源"
            value={storyboardTimelineSourceLabel(
              summary.timelineId,
              summary.timelineVersion,
              summary.generationSource,
            )}
          />
          <SupportMetaItem label="分镜" value={storyboardStatus} />
          <SupportMetaItem
            label="素材"
            value={`${summary.imageCount} 关键帧 · ${summary.videoCount} 视频`}
          />
        </div>
      </section>

      <WorkspaceStoryboardClipManagement
        episodeKey={episodeKey}
        selectedScriptId={selectedScriptId}
        selectedTimelineSpec={localTimelineSpec}
        selectedStoryboard={selectedStoryboard}
        normalizedScenes={normalizedScenes}
        resolvedVideos={resolvedVideos}
      />

      <OperatorPanel>
        <OperatorSectionHeader
          title="占位帧"
          subtitle={`${summary.frameCount} 个时间轴对齐镜头`}
        />
        {frames.length ? (
          <div className="divide-y divide-gray-100">
            {frames.map((frame) => (
              <StoryboardSupportFrameRow
                key={frame.id}
                frame={frame}
                selectedTimelineSpec={localTimelineSpec}
                showAlert={showAlert}
                onTimelineUpdated={handleTimelineUpdated}
              />
            ))}
          </div>
        ) : (
          <div className="p-4">
            <OperatorState
              title="暂无分镜占位"
              detail="当前剧本还没有可查看的时间轴占位帧。"
            />
          </div>
        )}
      </OperatorPanel>
    </div>
  );
}

function SupportMetaItem({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-1.5">
      <span className="text-slate-500">{label}</span>
      <span className="truncate font-medium text-slate-800">{value}</span>
    </span>
  );
}

function storyboardTimelineSourceLabel(
  timelineId: string | null,
  timelineVersion: string | null,
  generationSource: string | null,
) {
  return timelineId
    ? `Timeline ${timelineId} · v${timelineVersion ?? "?"}`
    : generationSource ?? "当前剧本 beat";
}
