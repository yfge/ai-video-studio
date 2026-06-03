"use client";

import Link from "next/link";
import { useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import {
  generateStoryboardFromAudioTimelineAsync,
  timelineAPI,
} from "@/utils/api/endpoints";
import type {
  TimelineResponse,
  TimelineStoryboardGridGenerateRequest,
} from "@/utils/api/types";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

interface WorkspaceStoryboardActionsProps {
  selectedScriptId?: number | null;
  selectedAudioTimeline?: Record<string, unknown> | null;
  selectedTimelineSpec?: TimelineResponse | null;
  videoClipCount: number;
  timelineHref: string;
  showAlert?: ShowAlert;
  onShowGrid: () => void;
  onGridTaskSubmitted: (taskId: number) => void;
}

export function WorkspaceStoryboardActions({
  selectedScriptId,
  selectedAudioTimeline,
  selectedTimelineSpec,
  videoClipCount,
  timelineHref,
  showAlert,
  onShowGrid,
  onGridTaskSubmitted,
}: WorkspaceStoryboardActionsProps) {
  const [generatingGrid, setGeneratingGrid] = useState(false);
  const [syncingAudioStoryboard, setSyncingAudioStoryboard] = useState(false);
  const canGenerateGrid = Boolean(
    selectedTimelineSpec && videoClipCount > 0 && !generatingGrid,
  );
  const canSyncAudioTimelineStoryboard = Boolean(
    !selectedTimelineSpec &&
      selectedAudioTimeline &&
      selectedScriptId &&
      !syncingAudioStoryboard,
  );

  const handleGenerateGrid = async () => {
    if (!selectedTimelineSpec) return;
    onShowGrid();
    setGeneratingGrid(true);
    try {
      const res = await timelineAPI.generateTimelineStoryboardGrid(
        selectedTimelineSpec.id,
        buildStoryboardGridGenerateRequest(
          selectedTimelineSpec,
          videoClipCount,
        ),
      );
      if (!res.success || !res.data) {
        showAlert?.({
          message: res.error || "宫格故事板任务提交失败",
          variant: "error",
        });
        return;
      }
      onGridTaskSubmitted(res.data.task_id);
      showAlert?.({
        message: `宫格故事板任务已提交 #${res.data.task_id}`,
        variant: "success",
      });
    } catch (error) {
      showAlert?.({
        message:
          error instanceof Error
            ? `宫格故事板任务提交失败：${error.message}`
            : "宫格故事板任务提交失败",
        variant: "error",
      });
    } finally {
      setGeneratingGrid(false);
    }
  };

  const handleSyncAudioTimelineStoryboard = async () => {
    if (!selectedScriptId) {
      showAlert?.({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    if (!selectedAudioTimeline) {
      showAlert?.({
        message: "请先生成时间轴，再同步分镜占位",
        variant: "warning",
      });
      return;
    }

    setSyncingAudioStoryboard(true);
    try {
      const res = await generateStoryboardFromAudioTimelineAsync(
        selectedScriptId,
        {
          overwrite_existing: false,
          min_pause_seconds: 1.5,
        },
      );
      if (!res.success || !res.data) {
        showAlert?.({
          message: res.error || "分镜占位任务提交失败",
          variant: "error",
        });
        return;
      }
      showAlert?.({
        message: `分镜占位任务已提交 #${res.data.task_id}`,
        variant: "success",
      });
    } catch (error) {
      showAlert?.({
        message:
          error instanceof Error
            ? `分镜占位任务提交失败：${error.message}`
            : "分镜占位任务提交失败",
        variant: "error",
      });
    } finally {
      setSyncingAudioStoryboard(false);
    }
  };

  return (
    <div className="flex flex-wrap justify-end gap-2">
      {selectedTimelineSpec ? (
        <button
          type="button"
          disabled={!canGenerateGrid}
          className={operatorButtonClass("primary")}
          onClick={handleGenerateGrid}
        >
          {generatingGrid ? "提交中..." : "生成宫格分镜"}
        </button>
      ) : (
        <button
          type="button"
          disabled={!canSyncAudioTimelineStoryboard}
          className={operatorButtonClass("primary")}
          onClick={handleSyncAudioTimelineStoryboard}
        >
          {syncingAudioStoryboard ? "提交中..." : "同步分镜占位"}
        </button>
      )}
      <Link href={timelineHref} className={operatorButtonClass("secondary")}>
        返回时间轴
      </Link>
    </div>
  );
}

function buildStoryboardGridGenerateRequest(
  timeline: TimelineResponse,
  videoClipCount: number,
): TimelineStoryboardGridGenerateRequest {
  return {
    expected_version: timeline.version,
    panel_count: Math.min(9, Math.max(2, videoClipCount || 9)),
    style: "3d_cartoon",
    generation_profile: "storyboard_grid",
    size: "1536x1536",
    aspect_ratio: "1:1",
  };
}
