"use client";

import { useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
} from "@/components/shared";
import type { NormalizedScene, TimelineResponse } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  buildStoryboardTimelineOverview,
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
  type StoryboardTimelineOverview,
} from "./WorkspaceStoryboardSupportModel";
import { WorkspaceStoryboardActions } from "./WorkspaceStoryboardActions";
import { WorkspaceStoryboardClipManagement } from "./WorkspaceStoryboardClipManagement";
import { StoryboardSupportFrameRow } from "./WorkspaceStoryboardFrameRow";

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
      <OperatorPanel>
        <OperatorSectionHeader
          title="分镜辅助工作区"
          subtitle="分镜按时间轴 beat 对齐，用于图像和视频生成"
          action={
            <WorkspaceStoryboardActions
              selectedScriptId={selectedScriptId}
              selectedAudioTimeline={selectedAudioTimeline}
              timelineHref={timelineHref}
              showAlert={showAlert}
            />
          }
        />
        <div className="mt-4 grid gap-3 text-xs text-gray-600 sm:grid-cols-3">
          <ContextCell
            label="时间轴来源"
            value={
              summary.timelineId
                ? `Timeline ${summary.timelineId} · v${
                    summary.timelineVersion ?? "?"
                  }`
                : summary.generationSource ?? "当前剧本 beat"
            }
          />
          <ContextCell label="分镜状态" value={storyboardStatus} />
          <ContextCell
            label="关键帧 / 视频"
            value={`${summary.imageCount} 关键帧 · ${summary.videoCount} 视频`}
          />
        </div>
        {timelineOverview ? (
          <StoryboardTimelineOverviewPanel overview={timelineOverview} />
        ) : null}
      </OperatorPanel>

      <WorkspaceStoryboardClipManagement
        episodeKey={episodeKey}
        selectedScriptId={selectedScriptId}
        selectedTimelineSpec={localTimelineSpec}
        selectedStoryboard={selectedStoryboard}
        normalizedScenes={normalizedScenes}
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

function ContextCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
      <div className="text-gray-500">{label}</div>
      <div className="mt-1 font-medium text-gray-800">{value}</div>
    </div>
  );
}

function StoryboardTimelineOverviewPanel({
  overview,
}: {
  overview: StoryboardTimelineOverview;
}) {
  return (
    <div className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">当前时间轴</div>
          <div className="mt-1 text-sm font-semibold text-gray-900">
            {overview.timelineLabel}
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-600">
            <span>状态 {overview.status ?? "未知"}</span>
            <span>时长 {overview.durationLabel}</span>
            <span>{overview.trackSummary}</span>
            <span>对白 {overview.dialogueClipCount}</span>
            <span>视频 {overview.videoClipCount}</span>
            {overview.audioVersion ? (
              <span>音频 v{overview.audioVersion}</span>
            ) : null}
          </div>
        </div>
        {overview.audioUrl ? (
          <div className="min-w-0 flex-1 basis-72">
            <div className="mb-1 text-xs text-gray-500">音轨</div>
            <audio
              aria-label="播放时间轴音轨"
              className="w-full"
              controls
              preload="none"
              src={overview.audioUrl}
            />
          </div>
        ) : (
          <div className="text-xs text-amber-700">暂无可播放音轨 URL</div>
        )}
      </div>
    </div>
  );
}
