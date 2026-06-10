"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { scriptAPI } from "@/utils/api/endpoints";
import type {
  NormalizedScene,
  Script,
  TimelineResponse,
} from "@/utils/api/types";
import { OperatorState } from "@/components/shared";
import { EpisodeTimelineWorkspace } from "./EpisodeTimelineWorkspace";
import { useTimelinePipelineTracking } from "./useTimelinePipelineTracking";

interface WorkspaceTimelineTabContentProps {
  episodeId: number | string;
  scripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  selectedTimelineSpec: TimelineResponse | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  initialSelectedClipId?: string | null;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;

  // Model selection
  timingModel: string;
  setTimingModel: (value: string) => void;

  // Alert
  showAlert: (options: {
    message: string;
    variant: "info" | "success" | "warning" | "error";
  }) => void;
}

export function WorkspaceTimelineTabContent({
  episodeId,
  scripts,
  selectedScriptId,
  selectedScript,
  selectedTimelineSpec,
  onTimelineUpdated,
  initialSelectedClipId,
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
  timingModel,
  setTimingModel,
  showAlert,
}: WorkspaceTimelineTabContentProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [pipelineBusy, setPipelineBusy] = useState(false);
  const [useDurationControl, setUseDurationControl] = useState(false);
  const { pipelineTask, trackPipelineTask } = useTimelinePipelineTracking({
    episodeId,
    selectedScriptId,
    onTimelineUpdated,
  });

  const autoTimelinePipelineRunId = searchParams.get("autoTimelinePipeline");

  const handleGenerateTimelinePipeline = useCallback(async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setPipelineBusy(true);
      const res = await scriptAPI.generateTimelinePipelineAsync(
        selectedScriptId,
        {
          timing_model: timingModel || undefined,
          // Use sensible defaults
          overwrite_audio: true,
          overwrite_timeline: true,
          overwrite_storyboard: true,
          min_pause_seconds: 1.5,
          use_duration_control: useDurationControl,
        },
      );
      if (res.success && res.data) {
        trackPipelineTask(res.data.task_id);
        showAlert({
          message: `一键流水线任务已提交（task_id=${res.data.task_id}），完成后自动刷新时间轴`,
          variant: "info",
        });
      } else {
        showAlert({
          message: `创建一键流水线任务失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("创建一键流水线任务失败:", error);
      showAlert({ message: "创建一键流水线任务失败", variant: "error" });
    } finally {
      setPipelineBusy(false);
    }
  }, [
    selectedScriptId,
    showAlert,
    timingModel,
    trackPipelineTask,
    useDurationControl,
  ]);

  useEffect(() => {
    if (!autoTimelinePipelineRunId || pipelineBusy || !selectedScriptId) return;

    try {
      const storageKey = `autoTimelinePipeline:${selectedScriptId}`;
      const lastRunId = window.sessionStorage.getItem(storageKey);
      if (lastRunId === autoTimelinePipelineRunId) return;
      window.sessionStorage.setItem(storageKey, autoTimelinePipelineRunId);
    } catch {
      // ignore
    }

    void handleGenerateTimelinePipeline();

    const params = new URLSearchParams(searchParams.toString());
    params.delete("autoTimelinePipeline");
    const next = params.toString();
    router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });
  }, [
    autoTimelinePipelineRunId,
    handleGenerateTimelinePipeline,
    pathname,
    pipelineBusy,
    router,
    searchParams,
    selectedScriptId,
  ]);

  const handleNavigateToTasks = useCallback(() => {
    router.push("/tasks");
  }, [router]);

  const handleNavigateToScript = useCallback(() => {
    if (selectedScript) {
      router.push(
        `/scripts/${selectedScript.business_id || selectedScript.id}`,
      );
    }
  }, [router, selectedScript]);

  const handleNavigateToStoryboard = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", "storyboard");
    if (selectedScriptId) {
      params.set("scriptId", String(selectedScriptId));
    }
    router.push(`${pathname}?${params.toString()}`);
  }, [pathname, router, searchParams, selectedScriptId]);

  const handleNavigateToCharacters = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", "characters");
    if (selectedScriptId) {
      params.set("scriptId", String(selectedScriptId));
    }
    router.push(`${pathname}?${params.toString()}`);
  }, [pathname, router, searchParams, selectedScriptId]);

  if (scripts.length === 0) {
    return (
      <OperatorState
        title="暂无剧本"
        detail="请先生成剧本，然后才能创建时间轴"
      />
    );
  }

  return (
    <EpisodeTimelineWorkspace
      episodeId={episodeId}
      selectedScriptId={selectedScriptId}
      selectedScript={selectedScript}
      selectedTimelineSpec={selectedTimelineSpec}
      onTimelineUpdated={onTimelineUpdated}
      initialSelectedClipId={initialSelectedClipId}
      selectedAudioTimeline={selectedAudioTimeline}
      selectedStoryboard={selectedStoryboard}
      normalizedScenes={normalizedScenes}
      normalizedScenesLoading={normalizedScenesLoading}
      normalizedScenesError={normalizedScenesError}
      pipelineBusy={pipelineBusy}
      timingModel={timingModel}
      setTimingModel={setTimingModel}
      useDurationControl={useDurationControl}
      setUseDurationControl={setUseDurationControl}
      onGenerateTimelinePipeline={handleGenerateTimelinePipeline}
      pipelineTask={pipelineTask}
      onNavigateToTasks={handleNavigateToTasks}
      onNavigateToScript={handleNavigateToScript}
      onNavigateToStoryboard={handleNavigateToStoryboard}
      onNavigateToCharacters={handleNavigateToCharacters}
    />
  );
}
