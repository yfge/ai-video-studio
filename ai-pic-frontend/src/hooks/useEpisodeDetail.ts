"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { episodeAPI, scriptAPI, taskAPI } from "@/utils/api/endpoints";
import type {
  Episode,
  Script,
  ScriptGenerationRequest,
  Task,
} from "@/utils/api/types";
import { useNormalizedScenes } from "@/hooks/useNormalizedScenes";
import { useTaskPolling, type TaskPollPair } from "@/hooks/useTaskPolling";
import { useEpisodeMetadata } from "@/hooks/useEpisodeMetadata";
import { sortScriptsNewestFirst } from "@/hooks/episode/scriptSort";
import { useSelectedScriptDetailHydration } from "@/hooks/episode/useSelectedScriptDetailHydration";
import { SCRIPT_GENERATION_DEFAULTS } from "@/utils/scriptGenerationDefaults";

export {
  asRecord,
  extractScenes,
  getSceneCount,
  getNumber,
  getString,
  parseMs,
} from "@/hooks/episodeDetailUtils";

export interface UseEpisodeDetailOptions {
  episodeKey: string;
  showAlert: (options: {
    message: string;
    variant: "info" | "success" | "warning" | "error";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
}

export function useEpisodeDetail({
  episodeKey,
  showAlert,
}: UseEpisodeDetailOptions) {
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [useAsync, setUseAsync] = useState(true);
  const [promptPreview, setPromptPreview] = useState("");
  const [selectedScriptId, setSelectedScriptId] = useState<number | null>(null);
  const [overwriteSceneAudio, setOverwriteSceneAudio] = useState(false);
  const [overwriteTimeline, setOverwriteTimeline] = useState(false);
  const [overwriteStoryboard, setOverwriteStoryboard] = useState(false);
  const [minPauseSeconds, setMinPauseSeconds] = useState(1.5);
  const [timingModel, setTimingModel] = useState<string>("");
  const [useDurationControl, setUseDurationControl] = useState(false);
  const [sceneAudioBusy, setSceneAudioBusy] = useState(false);
  const [timelineBusy, setTimelineBusy] = useState(false);
  const [storyboardBusy, setStoryboardBusy] = useState(false);

  const selectedScript =
    scripts.find((script) => script.id === selectedScriptId) ??
    scripts[0] ??
    null;

  const {
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    refreshNormalizedScenes,
  } = useNormalizedScenes(selectedScript?.id ?? null);
  useSelectedScriptDetailHydration(selectedScript, setScripts);
  const [sceneAudioTaskId, setSceneAudioTaskId] = useState<number | null>(null);
  const [timelineTaskId, setTimelineTaskId] = useState<number | null>(null);
  const [storyboardTaskId, setStoryboardTaskId] = useState<number | null>(null);
  const [sceneAudioTask, setSceneAudioTask] = useState<Task | null>(null);
  const [timelineTask, setTimelineTask] = useState<Task | null>(null);
  const [storyboardTask, setStoryboardTask] = useState<Task | null>(null);

  const [generateForm, setGenerateForm] = useState<ScriptGenerationRequest>(
    SCRIPT_GENERATION_DEFAULTS,
  );

  const [formats, setFormats] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [languages, setLanguages] = useState<
    Array<{ value: string; label: string }>
  >([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [episodeResponse, scriptsResponse] = await Promise.all([
        episodeAPI.getEpisode(episodeKey),
        scriptAPI.getEpisodeScripts(episodeKey),
      ]);

      if (episodeResponse.success && episodeResponse.data) {
        setEpisode(episodeResponse.data);
      }
      if (scriptsResponse.success && scriptsResponse.data) {
        setScripts(sortScriptsNewestFirst(scriptsResponse.data));
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [episodeKey, showAlert]);

  const loadOptions = useCallback(async () => {
    try {
      const [formatsResponse, languagesResponse] = await Promise.all([
        scriptAPI.getScriptFormats(),
        scriptAPI.getScriptLanguages(),
      ]);

      if (formatsResponse.success && formatsResponse.data) {
        setFormats(formatsResponse.data);
      }
      if (languagesResponse.success && languagesResponse.data) {
        setLanguages(languagesResponse.data);
      }
    } catch (error) {
      console.error("加载选项失败:", error);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadOptions();
  }, [loadData, loadOptions]);

  useEffect(() => {
    if (episode?.id) {
      setGenerateForm((prev) => ({ ...prev, episode_id: episode.id }));
    }
  }, [episode?.id]);

  useEffect(() => {
    if (sceneAudioTask?.status !== "completed") return;
    void refreshNormalizedScenes();
  }, [refreshNormalizedScenes, sceneAudioTask?.status]);

  const fetchTask = useCallback(async (taskId: number) => {
    try {
      const res = await taskAPI.getTask(String(taskId));
      if (res.success && res.data) return res.data;
      return null;
    } catch (error) {
      console.error("加载任务失败:", error);
      return null;
    }
  }, []);

  const taskPairs = useMemo<TaskPollPair[]>(
    () => [
      { id: sceneAudioTaskId, onUpdate: setSceneAudioTask },
      { id: timelineTaskId, onUpdate: setTimelineTask },
      { id: storyboardTaskId, onUpdate: setStoryboardTask },
    ],
    [sceneAudioTaskId, timelineTaskId, storyboardTaskId],
  );
  useTaskPolling({ taskPairs, fetchTask });

  useEffect(() => {
    if (sceneAudioTask?.status === "completed") {
      void loadData();
    }
  }, [sceneAudioTask?.status, loadData]);

  useEffect(() => {
    if (timelineTask?.status === "completed") {
      void loadData();
    }
  }, [timelineTask?.status, loadData]);

  useEffect(() => {
    if (storyboardTask?.status === "completed") {
      void loadData();
    }
  }, [storyboardTask?.status, loadData]);
  const metadata = useEpisodeMetadata(episode, selectedScript);

  return {
    episode,
    scripts,
    loading,
    selectedScript,
    selectedScriptId,
    setSelectedScriptId,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    episodeMeta: metadata.episodeMeta,
    selectedAudioTimeline: metadata.selectedAudioTimeline,
    selectedTimelineSpec: metadata.selectedTimelineSpec,
    setSelectedTimelineSpec: metadata.setSelectedTimelineSpec,
    selectedStoryboard: metadata.selectedStoryboard,
    formats,
    languages,
    generating,
    setGenerating,
    showGenerateForm,
    setShowGenerateForm,
    useAsync,
    setUseAsync,
    promptPreview,
    setPromptPreview,
    generateForm,
    setGenerateForm,
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
    useDurationControl,
    setUseDurationControl,
    sceneAudioBusy,
    setSceneAudioBusy,
    timelineBusy,
    setTimelineBusy,
    storyboardBusy,
    setStoryboardBusy,
    sceneAudioTaskId,
    setSceneAudioTaskId,
    timelineTaskId,
    setTimelineTaskId,
    storyboardTaskId,
    setStoryboardTaskId,
    sceneAudioTask,
    timelineTask,
    storyboardTask,
    loadData,
    setScripts,
    showAlert,
  };
}
