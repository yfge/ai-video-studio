"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Episode, NormalizedScene, Script, Task } from "@/utils/api";
import { scriptAPI } from "@/utils/api";
import { AudioTimelineSection } from "./AudioTimelineSection";

interface WorkspaceTimelineTabContentProps {
  episodeKey: string;
  episode: Episode;
  scripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  onSelectScript: (id: number | null) => void;
  episodeMeta: Record<string, unknown>;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;

  // Tasks
  sceneAudioTaskId: number | null;
  timelineTaskId: number | null;
  storyboardTaskId: number | null;
  sceneAudioTask: Task | null;
  timelineTask: Task | null;
  storyboardTask: Task | null;

  // Busy states
  sceneAudioBusy: boolean;
  timelineBusy: boolean;
  storyboardBusy: boolean;
  setSceneAudioBusy: (value: boolean) => void;
  setTimelineBusy: (value: boolean) => void;
  setStoryboardBusy: (value: boolean) => void;

  // Task setters
  setSceneAudioTaskId: (value: number | null) => void;
  setTimelineTaskId: (value: number | null) => void;
  setStoryboardTaskId: (value: number | null) => void;

  // Overwrite options
  overwriteSceneAudio: boolean;
  setOverwriteSceneAudio: (value: boolean) => void;
  overwriteTimeline: boolean;
  setOverwriteTimeline: (value: boolean) => void;
  overwriteStoryboard: boolean;
  setOverwriteStoryboard: (value: boolean) => void;
  minPauseSeconds: number;
  setMinPauseSeconds: (value: number) => void;
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
  episodeMeta,
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
  sceneAudioTaskId,
  timelineTaskId,
  storyboardTaskId,
  sceneAudioTask,
  timelineTask,
  storyboardTask,
  sceneAudioBusy,
  timelineBusy,
  storyboardBusy,
  setSceneAudioBusy,
  setTimelineBusy,
  setStoryboardBusy,
  setSceneAudioTaskId,
  setTimelineTaskId,
  setStoryboardTaskId,
  overwriteSceneAudio,
  setOverwriteSceneAudio,
  overwriteTimeline,
  setOverwriteTimeline,
  overwriteStoryboard,
  setOverwriteStoryboard,
  minPauseSeconds,
  setMinPauseSeconds,
  timingModel,
  setTimingModel,
  showAlert,
}: WorkspaceTimelineTabContentProps) {
  const router = useRouter();

  const handleGenerateSceneDialogueAudio = useCallback(async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setSceneAudioBusy(true);
      const res = await scriptAPI.generateSceneDialogueAudioAsync(selectedScriptId, {
        overwrite_audio: overwriteSceneAudio,
        overwrite_beats: true,
        timing_model: timingModel || undefined,
      });
      if (res.success && res.data) {
        setSceneAudioTaskId(res.data.task_id);
        showAlert({ message: `对白音轨任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建对白音轨任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建对白音轨任务失败:", error);
      showAlert({ message: "创建对白音轨任务失败", variant: "error" });
    } finally {
      setSceneAudioBusy(false);
    }
  }, [selectedScriptId, overwriteSceneAudio, timingModel, setSceneAudioBusy, setSceneAudioTaskId, showAlert]);

  const handleGenerateAudioTimeline = useCallback(async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setTimelineBusy(true);
      const res = await scriptAPI.generateAudioTimelineAsync(selectedScriptId, { overwrite: overwriteTimeline });
      if (res.success && res.data) {
        setTimelineTaskId(res.data.task_id);
        showAlert({ message: `时间轴任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建时间轴任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建时间轴任务失败:", error);
      showAlert({ message: "创建时间轴任务失败", variant: "error" });
    } finally {
      setTimelineBusy(false);
    }
  }, [selectedScriptId, overwriteTimeline, setTimelineBusy, setTimelineTaskId, showAlert]);

  const handleGenerateStoryboardFromAudioTimeline = useCallback(async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setStoryboardBusy(true);
      const res = await scriptAPI.generateStoryboardFromAudioTimelineAsync(selectedScriptId, {
        overwrite_existing: overwriteStoryboard,
        min_pause_seconds: minPauseSeconds,
      });
      if (res.success && res.data) {
        setStoryboardTaskId(res.data.task_id);
        showAlert({ message: `分镜占位任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建分镜占位任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建分镜占位任务失败:", error);
      showAlert({ message: "创建分镜占位任务失败", variant: "error" });
    } finally {
      setStoryboardBusy(false);
    }
  }, [selectedScriptId, overwriteStoryboard, minPauseSeconds, setStoryboardBusy, setStoryboardTaskId, showAlert]);

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
      episodeMeta={episodeMeta}
      selectedAudioTimeline={selectedAudioTimeline}
      selectedStoryboard={selectedStoryboard}
      normalizedScenes={normalizedScenes}
      normalizedScenesLoading={normalizedScenesLoading}
      normalizedScenesError={normalizedScenesError}
      sceneAudioTaskId={sceneAudioTaskId}
      timelineTaskId={timelineTaskId}
      storyboardTaskId={storyboardTaskId}
      sceneAudioTask={sceneAudioTask}
      timelineTask={timelineTask}
      storyboardTask={storyboardTask}
      sceneAudioBusy={sceneAudioBusy}
      timelineBusy={timelineBusy}
      storyboardBusy={storyboardBusy}
      overwriteSceneAudio={overwriteSceneAudio}
      setOverwriteSceneAudio={setOverwriteSceneAudio}
      overwriteTimeline={overwriteTimeline}
      setOverwriteTimeline={setOverwriteTimeline}
      overwriteStoryboard={overwriteStoryboard}
      setOverwriteStoryboard={setOverwriteStoryboard}
      minPauseSeconds={minPauseSeconds}
      setMinPauseSeconds={setMinPauseSeconds}
      timingModel={timingModel}
      setTimingModel={setTimingModel}
      onGenerateSceneDialogueAudio={handleGenerateSceneDialogueAudio}
      onGenerateAudioTimeline={handleGenerateAudioTimeline}
      onGenerateStoryboardFromAudioTimeline={handleGenerateStoryboardFromAudioTimeline}
      onNavigateToTasks={handleNavigateToTasks}
      onNavigateToScript={handleNavigateToScript}
    />
  );
}
