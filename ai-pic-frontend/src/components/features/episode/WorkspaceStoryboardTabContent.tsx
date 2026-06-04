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
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
} from "./WorkspaceStoryboardSupportModel";
import { WorkspaceStoryboardActions } from "./WorkspaceStoryboardActions";
import { StoryboardSupportFrameRow } from "./WorkspaceStoryboardFrameRow";
import {
  countTimelineVideoClips,
  WorkspaceStoryboardGridContent,
} from "./WorkspaceStoryboardGridContent";

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
  const [mode, setMode] = useState<"frames" | "grid">("frames");
  const [gridTaskId, setGridTaskId] = useState<number | null>(null);
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
  const videoClipCount = countTimelineVideoClips(localTimelineSpec);
  const summary = buildStoryboardSupportSummary(
    selectedStoryboard,
    localTimelineSpec,
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
              selectedTimelineSpec={localTimelineSpec}
              videoClipCount={videoClipCount}
              timelineHref={timelineHref}
              showAlert={showAlert}
              onShowGrid={() => setMode("grid")}
              onGridTaskSubmitted={setGridTaskId}
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
          <ContextCell
            label="分镜状态"
            value={storyboardStatus}
          />
          <ContextCell
            label="关键帧 / 视频"
            value={`${summary.imageCount} 关键帧 · ${summary.videoCount} 视频`}
          />
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-md border border-gray-200 bg-white p-1 text-xs">
            <ModeButton
              active={mode === "frames"}
              label="逐镜头"
              onClick={() => setMode("frames")}
            />
            <ModeButton
              active={mode === "grid"}
              label="宫格故事板"
              onClick={() => setMode("grid")}
            />
          </div>
        </div>
      </OperatorPanel>

      {mode === "frames" ? (
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
      ) : (
        <WorkspaceStoryboardGridContent
          selectedTimelineSpec={localTimelineSpec}
          gridTaskId={gridTaskId}
        />
      )}
    </div>
  );
}

function ModeButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded px-3 py-1.5 font-medium",
        active ? "bg-gray-900 text-white" : "text-gray-600 hover:text-gray-950",
      ].join(" ")}
    >
      {label}
    </button>
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
