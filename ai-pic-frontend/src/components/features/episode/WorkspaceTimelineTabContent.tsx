"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import type { NormalizedScene, Script } from "@/utils/api";
import { scriptAPI } from "@/utils/api";
import { AudioTimelineSection } from "./AudioTimelineSection";

interface WorkspaceTimelineTabContentProps {
  scripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  onSelectScript: (id: number | null) => void;
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
  scripts,
  selectedScriptId,
  selectedScript,
  onSelectScript,
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
  timingModel,
  setTimingModel,
  showAlert,
}: WorkspaceTimelineTabContentProps) {
  const router = useRouter();
  const [pipelineBusy, setPipelineBusy] = useState(false);
  const [pipelineTaskId, setPipelineTaskId] = useState<number | null>(null);

  const handleGenerateTimelinePipeline = useCallback(async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setPipelineBusy(true);
      const res = await scriptAPI.generateTimelinePipelineAsync(selectedScriptId, {
        timing_model: timingModel || undefined,
        // Use sensible defaults
        overwrite_audio: true,
        overwrite_timeline: true,
        overwrite_storyboard: true,
        min_pause_seconds: 1.5,
      });
      if (res.success && res.data) {
        setPipelineTaskId(res.data.task_id);
        showAlert({
          message: `一键流水线任务已创建（task_id=${res.data.task_id}）`,
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
  }, [selectedScriptId, timingModel, showAlert]);

  const handleNavigateToTasks = useCallback(() => {
    router.push("/tasks");
  }, [router]);

  const handleNavigateToScript = useCallback(() => {
    if (selectedScript) {
      router.push(`/scripts/${selectedScript.business_id || selectedScript.id}`);
    }
  }, [router, selectedScript]);

  if (scripts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无剧本</h3>
        <p className="text-gray-500 mb-4">请先生成剧本，然后才能创建时间轴</p>
      </div>
    );
  }

  return (
    <AudioTimelineSection
      scripts={scripts}
      selectedScriptId={selectedScriptId}
      selectedScript={selectedScript}
      onSelectScript={onSelectScript}
      selectedAudioTimeline={selectedAudioTimeline}
      selectedStoryboard={selectedStoryboard}
      normalizedScenes={normalizedScenes}
      normalizedScenesLoading={normalizedScenesLoading}
      normalizedScenesError={normalizedScenesError}
      pipelineBusy={pipelineBusy}
      timingModel={timingModel}
      setTimingModel={setTimingModel}
      onGenerateTimelinePipeline={handleGenerateTimelinePipeline}
      pipelineTaskId={pipelineTaskId}
      onNavigateToTasks={handleNavigateToTasks}
      onNavigateToScript={handleNavigateToScript}
    />
  );
}
